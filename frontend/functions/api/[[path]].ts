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

  // 2. Build Target URL strictly against fixed backend origin (blocks open proxy attacks)
  const targetUrl = new URL(clientUrl.pathname + clientUrl.search, backendOrigin);

  // 3. Clone and Sanitize Headers
  const proxyHeaders = new Headers(request.headers);
  proxyHeaders.set("Host", backendOrigin.host);
  proxyHeaders.set("X-Forwarded-Host", clientUrl.host);
  proxyHeaders.set("X-Forwarded-Proto", "https");

  // 4. Overwrite Spoofable Client IP Headers with Trusted Cloudflare IP
  const trustedClientIp = request.headers.get("CF-Connecting-IP") || "";
  proxyHeaders.set("CF-Connecting-IP", trustedClientIp);
  proxyHeaders.set("X-Forwarded-For", trustedClientIp);

  // 5. Inject Server-Side Shared Proxy Secret (never exposed to client browser)
  proxyHeaders.set("X-HealthAware-Proxy-Secret", env.PROXY_SECRET);

  const method = request.method.toUpperCase();
  const isBodyAllowed = !["GET", "HEAD"].includes(method);

  try {
    // 6. Forward Subrequest to Render
    const upstreamResponse = await fetch(targetUrl.toString(), {
      method,
      headers: proxyHeaders,
      body: isBodyAllowed ? request.body : null,
      redirect: "manual",
    });

    // 7. Reconstruct Response Preserving Set-Cookie & Status
    const responseHeaders = new Headers(upstreamResponse.headers);

    // Host-only cookie preservation
    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    // 8. Structured Cold-Start / Timeout Error Handling
    return new Response(
      JSON.stringify({
        error: {
          code: "BACKEND_UNAVAILABLE",
          message: "The backend service is starting up or temporarily unreachable. Please retry in a moment.",
        },
      }),
      {
        status: 503,
        headers: {
          "Content-Type": "application/json",
          "Retry-After": "10",
        },
      }
    );
  }
};
