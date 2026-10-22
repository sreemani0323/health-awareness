interface Env {
  RENDER_BACKEND_URL: string;
  PROXY_SECRET: string;
}

export const onRequest: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  // 1. Verify Configuration
  if (!env.RENDER_BACKEND_URL || !env.PROXY_SECRET) {
    return new Response(
      JSON.stringify({
        error: {
          code: "CONFIG_ERROR",
          message: "Upstream backend or proxy credentials are not configured.",
        },
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  const backendOrigin = new URL(env.RENDER_BACKEND_URL);
  const clientUrl = new URL(request.url);

  // 2. Strict CORS policy for authorized HealthAware web and native origins
  const ALLOWED_ORIGINS = new Set([
    "https://health-awareness.pages.dev",
    "https://localhost",
    "http://localhost",
    "capacitor://localhost",
  ]);

  const origin = request.headers.get("Origin");
  const isAllowedOrigin = origin && ALLOWED_ORIGINS.has(origin);

  // Handle CORS preflight (OPTIONS)
  if (request.method.toUpperCase() === "OPTIONS") {
    if (isAllowedOrigin) {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": origin,
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
          "Access-Control-Allow-Headers":
            "Content-Type, Authorization, X-Requested-With, X-CSRF-TOKEN, X-HealthAware-Proxy-Secret",
          "Access-Control-Allow-Credentials": "true",
          "Access-Control-Max-Age": "86400",
          "Vary": "Origin",
        },
      });
    }
  }

  // 3. Build Target URL strictly against fixed backend origin (blocks open proxy attacks)
  const targetUrl = new URL(clientUrl.pathname + clientUrl.search, backendOrigin);

  // 4. Clone and Sanitize Headers
  const proxyHeaders = new Headers(request.headers);
  proxyHeaders.set("Host", backendOrigin.host);
  proxyHeaders.set("X-Forwarded-Host", clientUrl.host);
  proxyHeaders.set("X-Forwarded-Proto", "https");

  // 5. Overwrite Spoofable Client IP Headers with Trusted Cloudflare IP
  const trustedClientIp = request.headers.get("CF-Connecting-IP") || "";
  proxyHeaders.set("CF-Connecting-IP", trustedClientIp);
  proxyHeaders.set("X-Forwarded-For", trustedClientIp);

  // 6. Inject Server-Side Shared Proxy Secret (never exposed to client browser)
  proxyHeaders.set("X-HealthAware-Proxy-Secret", env.PROXY_SECRET);

  const method = request.method.toUpperCase();
  const isBodyAllowed = !["GET", "HEAD"].includes(method);

  try {
    // 7. Forward Subrequest to Render
    const upstreamResponse = await fetch(targetUrl.toString(), {
      method,
      headers: proxyHeaders,
      body: isBodyAllowed ? request.body : null,
      redirect: "manual",
    });

    // 8. Reconstruct Response Preserving Set-Cookie & Status with CORS headers
    const responseHeaders = new Headers(upstreamResponse.headers);
    if (isAllowedOrigin) {
      responseHeaders.set("Access-Control-Allow-Origin", origin);
      responseHeaders.set("Access-Control-Allow-Credentials", "true");
      responseHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD");
      responseHeaders.set(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization, X-Requested-With, X-CSRF-TOKEN, X-HealthAware-Proxy-Secret"
      );
      responseHeaders.set("Vary", "Origin");
    }

    // Host-only cookie preservation
    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    // 9. Structured Cold-Start / Timeout Error Handling
    const errHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      "Retry-After": "10",
    };
    if (isAllowedOrigin) {
      errHeaders["Access-Control-Allow-Origin"] = origin;
      errHeaders["Access-Control-Allow-Credentials"] = "true";
      errHeaders["Vary"] = "Origin";
    }

    return new Response(
      JSON.stringify({
        error: {
          code: "BACKEND_UNAVAILABLE",
          message: "The backend service is starting up or temporarily unreachable. Please retry in a moment.",
        },
      }),
      {
        status: 503,
        headers: errHeaders,
      }
    );
  }
};
