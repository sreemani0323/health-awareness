import {
  HttpInterceptorFn,
  HttpRequest,
  HttpHandlerFn,
  HttpEvent,
  HttpErrorResponse,
  HttpContextToken,
} from '@angular/common/http';
import { defer, Observable, throwError, timer, TimeoutError } from 'rxjs';
import { timeout, retry, catchError } from 'rxjs/operators';

/**
 * Token to configure per-attempt timeout (default 10,000ms).
 * Bounds each individual network transmission attempt.
 */
export const PER_ATTEMPT_TIMEOUT_MS = new HttpContextToken<number>(() => 10000);

/**
 * Token to configure overall request budget/deadline across all retries and backoff delays (default 25,000ms).
 * Guarantees that the entire request lifecycle never exceeds this hard ceiling.
 */
export const OVERALL_TIMEOUT_MS = new HttpContextToken<number>(() => 25000);

/**
 * Token to override default timeout per request if needed (alias for PER_ATTEMPT_TIMEOUT_MS for backward compatibility).
 */
export const REQUEST_TIMEOUT_MS = PER_ATTEMPT_TIMEOUT_MS;

/**
 * Token to explicitly bypass automatic retries even for GET requests.
 */
export const BYPASS_RETRY = new HttpContextToken<boolean>(() => false);

/**
 * Safe HTTP methods that are idempotent and eligible for transient retry.
 */
const IDEMPOTENT_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);

/**
 * HTTP status codes that represent transient infrastructure / server failures
 * eligible for retry on safe idempotent requests.
 */
const RETRYABLE_STATUS_CODES = new Set([0, 502, 503, 504]);

/**
 * Sanitizes technical error messages to ensure internal infrastructure,
 * database URLs, stack traces, and credentials are never exposed to learners or staff.
 */
export function sanitizeErrorMessage(rawMessage: string): string {
  if (!rawMessage) return 'An unexpected error occurred.';

  // Mask database URLs, credentials, hostnames, and stack traces
  let sanitized = rawMessage
    .replace(/postgresql\+?[^:\s]*:\/\/[^\s]+/gi, '[database-url]')
    .replace(/postgres:\/\/[^\s]+/gi, '[database-url]')
    .replace(/password=[^\s;&]+/gi, 'password=[redacted]')
    .replace(/[a-zA-Z0-9.-]+\.neon\.tech/gi, '[database-host]')
    .replace(/Traceback \(most recent call last\):[\s\S]*/gi, '')
    .replace(/[A-Z]:\\[^\s]+/g, '[file-path]')
    .replace(/\/home\/[^\s]+/g, '[file-path]')
    .replace(/\/var\/[^\s]+/g, '[file-path]');

  return sanitized.trim();
}

/**
 * Resolves a clear, actionable, user-friendly error message based on HTTP status code.
 */
export function getActionableErrorMessage(
  error: unknown,
  status?: number
): string {
  if (error instanceof TimeoutError || (error as any)?.name === 'TimeoutError') {
    return 'The request timed out. Please check your internet connection and try again.';
  }

  const httpStatus =
    status !== undefined
      ? status
      : error instanceof HttpErrorResponse
      ? error.status
      : 0;

  switch (httpStatus) {
    case 0:
      return 'Unable to reach the server. Please check your internet connection.';
    case 401:
      return 'Your session has expired or authentication is required. Please sign in again.';
    case 403:
      return 'You do not have permission to access or perform this action.';
    case 404:
      return 'The requested health resource or record was not found.';
    case 409:
      return 'A conflict occurred with existing records. Please refresh and try again.';
    case 422: {
      if (error instanceof HttpErrorResponse && error.error?.error?.message) {
        return sanitizeErrorMessage(error.error.error.message);
      }
      return 'The submitted information contains validation errors. Please check your inputs and try again.';
    }
    case 429:
      return 'Too many requests. Please wait a moment before trying again.';
    case 500:
      return 'An unexpected server error occurred. Our team has been notified. Please try again later.';
    case 502:
      return 'The server gateway is temporarily unreachable. Please check back shortly.';
    case 503:
      return 'The service is temporarily unavailable or initializing. Please retry in a moment.';
    case 504:
      return 'The server took too long to respond. Please check your connection and try again.';
    default:
      if (error instanceof HttpErrorResponse && error.error?.error?.message) {
        return sanitizeErrorMessage(error.error.error.message);
      }
      return 'An unexpected error occurred. Please try again.';
  }
}

/**
 * Angular HTTP Interceptor that enforces:
 * 1. Bounded per-attempt network timeouts (default 10s via PER_ATTEMPT_TIMEOUT_MS).
 * 2. Exponential-backoff retries strictly for safe, idempotent requests (GET, HEAD, max 2 retries).
 * 3. Never retrying non-idempotent operations (POST, PUT, DELETE) like concern submissions or auth.
 * 4. Overall request deadline ceiling (default 25s via OVERALL_TIMEOUT_MS) across retries and backoff.
 * 5. User-friendly, actionable error formatting with leakage sanitization for all response codes.
 */
export const apiTimeoutRetryInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {
  const perAttemptTimeoutMs = req.context.get(PER_ATTEMPT_TIMEOUT_MS);
  const overallTimeoutMs = req.context.get(OVERALL_TIMEOUT_MS);
  const bypassRetry = req.context.get(BYPASS_RETRY);
  const isIdempotent = IDEMPOTENT_METHODS.has(req.method.toUpperCase());

  return defer(() => next(req)).pipe(
    // 1. Bound per-attempt execution time ceiling
    timeout({
      each: perAttemptTimeoutMs,
      with: () => throwError(() => new TimeoutError()),
    }),

    // 2. Retry ONLY safe, idempotent requests with bounded exponential backoff
    retry({
      count: isIdempotent && !bypassRetry ? 2 : 0,
      delay: (error: unknown, retryCount: number) => {
        // Never retry if method is non-idempotent
        if (!isIdempotent || bypassRetry) {
          return throwError(() => error);
        }

        const isTimeout =
          error instanceof TimeoutError ||
          (error as any)?.name === 'TimeoutError';
        const isHttpError = error instanceof HttpErrorResponse;
        const statusCode = isHttpError ? error.status : isTimeout ? 0 : -1;

        if (!isTimeout && !RETRYABLE_STATUS_CODES.has(statusCode)) {
          // Do not retry 4xx errors (400, 401, 403, 404, 409, 422, 429) or 500
          return throwError(() => error);
        }

        // Bounded exponential backoff: ~750ms * 2^(retryCount-1) + jitter (max 2500ms)
        const baseDelay = Math.min(750 * Math.pow(2, retryCount - 1), 2000);
        const jitter = Math.floor(Math.random() * 250);
        return timer(baseDelay + jitter);
      },
    }),

    // 3. Bound overall request duration across all attempts and backoff delays
    timeout({
      first: overallTimeoutMs,
      with: () => throwError(() => new TimeoutError()),
    }),

    // 4. Catch final error and standardize actionable error messages
    catchError((error: unknown) => {
      const actionableMsg = getActionableErrorMessage(error);

      if (error instanceof HttpErrorResponse) {
        // Create an augmented response with sanitized friendly message
        const sanitizedErrorBody =
          typeof error.error === 'object' && error.error !== null
            ? {
                ...error.error,
                error: {
                  ...(error.error.error || {}),
                  message: actionableMsg,
                },
                userMessage: actionableMsg,
              }
            : {
                error: {
                  code: error.status === 0 ? 'NETWORK_ERROR' : `HTTP_${error.status}`,
                  message: actionableMsg,
                },
                userMessage: actionableMsg,
              };

        const enhancedError = new HttpErrorResponse({
          error: sanitizedErrorBody,
          headers: error.headers,
          status: error.status,
          statusText: error.statusText,
          url: error.url || req.url,
        });

        return throwError(() => enhancedError);
      }

      if (error instanceof TimeoutError || (error as any)?.name === 'TimeoutError') {
        const timeoutError = new HttpErrorResponse({
          error: {
            error: {
              code: 'TIMEOUT',
              message: actionableMsg,
            },
            userMessage: actionableMsg,
          },
          status: 0,
          statusText: 'Timeout',
          url: req.url,
        });
        return throwError(() => timeoutError);
      }

      return throwError(() => error);
    })
  );
};
