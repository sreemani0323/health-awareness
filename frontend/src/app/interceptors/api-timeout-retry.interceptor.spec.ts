import { describe, it, expect, vi } from 'vitest';
import {
  HttpRequest,
  HttpErrorResponse,
  HttpResponse,
  HttpContext,
} from '@angular/common/http';
import { of, throwError, firstValueFrom, Observable } from 'rxjs';
import {
  apiTimeoutRetryInterceptor,
  REQUEST_TIMEOUT_MS,
  PER_ATTEMPT_TIMEOUT_MS,
  OVERALL_TIMEOUT_MS,
  BYPASS_RETRY,
  getActionableErrorMessage,
  sanitizeErrorMessage,
} from './api-timeout-retry.interceptor';

describe('ApiTimeoutRetryInterceptor', () => {
  describe('Error sanitization & Actionable messages', () => {
    it('masks database connection URLs, passwords, and hostnames', () => {
      const rawUrl =
        'OperationalError: connection to postgresql://user:secret123@ep-cool-db.neon.tech/db failed. password=secret123';
      const sanitizedUrl = sanitizeErrorMessage(rawUrl);
      expect(sanitizedUrl).not.toContain('postgresql://');
      expect(sanitizedUrl).not.toContain('secret123');
      expect(sanitizedUrl).not.toContain('ep-cool-db.neon.tech');
      expect(sanitizedUrl).toContain('[database-url]');
      expect(sanitizedUrl).toContain('password=[redacted]');

      const rawHost = 'Could not connect to host ep-cool-db.neon.tech on port 5432';
      const sanitizedHost = sanitizeErrorMessage(rawHost);
      expect(sanitizedHost).toContain('[database-host]');
      expect(sanitizedHost).not.toContain('ep-cool-db.neon.tech');
    });

    it('strips backend python tracebacks', () => {
      const raw =
        'Error occurred. Traceback (most recent call last):\n  File "app.py", line 42\nException: boom';
      const sanitized = sanitizeErrorMessage(raw);
      expect(sanitized).not.toContain('Traceback');
      expect(sanitized).not.toContain('line 42');
    });

    it('returns actionable messages for 401, 403, 404, 409, 422, 429, 500, 502, 503, 504', () => {
      expect(getActionableErrorMessage(null, 401)).toContain('session has expired');
      expect(getActionableErrorMessage(null, 403)).toContain('permission');
      expect(getActionableErrorMessage(null, 404)).toContain('not found');
      expect(getActionableErrorMessage(null, 409)).toContain('conflict');
      expect(getActionableErrorMessage(null, 422)).toContain('validation errors');
      expect(getActionableErrorMessage(null, 429)).toContain('Too many requests');
      expect(getActionableErrorMessage(null, 500)).toContain('server error');
      expect(getActionableErrorMessage(null, 502)).toContain('gateway');
      expect(getActionableErrorMessage(null, 503)).toContain('temporarily unavailable');
      expect(getActionableErrorMessage(null, 504)).toContain('took too long to respond');
      expect(getActionableErrorMessage(null, 0)).toContain('Unable to reach the server');
    });
  });

  describe('Interceptor execution and retry policy', () => {
    it('passes successful GET requests through directly', async () => {
      const req = new HttpRequest('GET', '/api/v1/topics');
      const expectedResponse = new HttpResponse({ status: 200, body: { data: [] } });
      const nextFn = vi.fn().mockReturnValue(of(expectedResponse));

      const response = await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
      expect(response).toBe(expectedResponse);
      expect(nextFn).toHaveBeenCalledTimes(1);
    });

    it('does NOT retry non-idempotent POST requests on 503 or error', async () => {
      const req = new HttpRequest('POST', '/api/v1/concerns', { description: 'Drain issue' });
      const errorResponse = new HttpErrorResponse({
        status: 503,
        statusText: 'Service Unavailable',
        error: { message: 'Database busy' },
      });
      const nextFn = vi.fn().mockReturnValue(throwError(() => errorResponse));

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have thrown');
      } catch (err: any) {
        expect(err.status).toBe(503);
        expect(err.error.userMessage).toContain('temporarily unavailable');
        // Critical: Must only have been called ONCE. Never retried!
        expect(nextFn).toHaveBeenCalledTimes(1);
      }
    });

    it('does NOT retry authentication requests on 401', async () => {
      const req = new HttpRequest('POST', '/api/v1/learner/auth/login', { email: 'a@b.com' });
      const errorResponse = new HttpErrorResponse({
        status: 401,
        statusText: 'Unauthorized',
      });
      const nextFn = vi.fn().mockReturnValue(throwError(() => errorResponse));

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have thrown');
      } catch (err: any) {
        expect(err.status).toBe(401);
        expect(err.error.userMessage).toContain('session has expired');
        expect(nextFn).toHaveBeenCalledTimes(1);
      }
    });

    it('does NOT retry 404 or 422 client errors on GET', async () => {
      const req = new HttpRequest('GET', '/api/v1/topics/unknown-topic');
      const errorResponse = new HttpErrorResponse({
        status: 404,
        statusText: 'Not Found',
      });
      const nextFn = vi.fn().mockReturnValue(throwError(() => errorResponse));

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have thrown');
      } catch (err: any) {
        expect(err.status).toBe(404);
        expect(err.error.userMessage).toContain('not found');
        expect(nextFn).toHaveBeenCalledTimes(1);
      }
    });

    it('does NOT retry when BYPASS_RETRY token is explicitly set to true', async () => {
      const context = new HttpContext().set(BYPASS_RETRY, true);
      const req = new HttpRequest('GET', '/api/v1/topics', { context });
      const errorResponse = new HttpErrorResponse({
        status: 503,
        statusText: 'Service Unavailable',
      });
      const nextFn = vi.fn().mockReturnValue(throwError(() => errorResponse));

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have thrown');
      } catch (err: any) {
        expect(err.status).toBe(503);
        expect(nextFn).toHaveBeenCalledTimes(1);
      }
    });

    it('triggers per-attempt timeout when single network attempt hangs', async () => {
      const context = new HttpContext()
        .set(PER_ATTEMPT_TIMEOUT_MS, 40)
        .set(BYPASS_RETRY, true);
      const req = new HttpRequest('GET', '/api/v1/slow', { context });

      // Simulate a hung connection that never emits
      const nextFn = vi.fn().mockReturnValue(new Observable());

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have timed out');
      } catch (err: any) {
        expect(err.status).toBe(0);
        expect(err.error.error.code).toBe('TIMEOUT');
        expect(err.error.userMessage).toContain('timed out');
        expect(nextFn).toHaveBeenCalledTimes(1);
      }
    });

    it('enforces overall request budget ceiling across retries', async () => {
      // Set short overall timeout 60ms, with per-attempt timeout 50ms and retries enabled
      const context = new HttpContext()
        .set(PER_ATTEMPT_TIMEOUT_MS, 30)
        .set(OVERALL_TIMEOUT_MS, 60);
      const req = new HttpRequest('GET', '/api/v1/slow-all-attempts', { context });

      // Return hung observable on each attempt
      const nextFn = vi.fn().mockImplementation(() => new Observable());

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have hit overall deadline');
      } catch (err: any) {
        expect(err.status).toBe(0);
        expect(err.error.error.code).toBe('TIMEOUT');
        expect(err.error.userMessage).toContain('timed out');
      }
    });

    it('retries idempotent GET requests on 503 up to 2 times before surfacing failure', async () => {
      const context = new HttpContext().set(OVERALL_TIMEOUT_MS, 5000);
      const req = new HttpRequest('GET', '/api/v1/topics', { context });
      const error503 = new HttpErrorResponse({
        status: 503,
        statusText: 'Service Unavailable',
      });
      const nextFn = vi.fn().mockReturnValue(throwError(() => error503));

      try {
        await firstValueFrom(apiTimeoutRetryInterceptor(req, nextFn));
        expect.unreachable('Should have thrown 503');
      } catch (err: any) {
        expect(err.status).toBe(503);
        // 1 initial call + 2 retries = 3 calls
        expect(nextFn).toHaveBeenCalledTimes(3);
        expect(err.error.userMessage).toContain('temporarily unavailable');
      }
    }, 10000);
  });
});
