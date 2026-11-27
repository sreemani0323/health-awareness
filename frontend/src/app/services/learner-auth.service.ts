import { Injectable, signal, computed, inject } from '@angular/core';
import { ApiConfigService } from './api-config.service';
import { SecureStorageService } from './secure-storage.service';

export interface LearnerUser {
  id: string;
  name?: string;
  email?: string;
}

export interface RemoteResumeState {
  lessonId: string;
  lessonTitle: string;
  topicId: string;
  cardIndex: number;
  totalCards: number;
  updatedAt: string;
}

export interface RemoteMilestone {
  id: string;
  title: string;
  description: string;
  icon: string;
  achievedAt: string;
}

export interface RemoteLearnerProgress {
  version: number;
  last_lesson: RemoteResumeState | null;
  completed_lesson_ids: string[];
  completed_activity_ids: string[];
  achieved_milestones: RemoteMilestone[];
  client_updated_at?: string;
  updated_at?: string;
}

const TOKEN_KEY = 'healthaware_learner_jwt';
const USER_KEY = 'healthaware_learner_profile';

@Injectable({ providedIn: 'root' })
export class LearnerAuthService {
  private readonly tokenKey = TOKEN_KEY;
  private readonly userKey = USER_KEY;
  private readonly apiConfig = inject(ApiConfigService);
  private readonly secureStorage = inject(SecureStorageService);
  private cachedToken: string | null = null;

  readonly isAuthenticated = signal<boolean>(false);
  readonly currentUser = signal<LearnerUser | null>(null);
  readonly syncStatus = signal<'idle' | 'syncing' | 'synced' | 'error'>('idle');
  readonly lastSyncedAt = signal<string | null>(null);
  readonly errorMessage = signal<string | null>(null);

  readonly displayName = computed(() => {
    const user = this.currentUser();
    if (!user) return 'Learner';
    return user.name || user.email || 'Learner';
  });

  constructor() {
    this.restoreSession();
  }

  /**
   * Restores stored JWT and learner profile from secure client storage.
   */
  private async restoreSession(): Promise<void> {
    try {
      const token = await this.secureStorage.getItem(this.tokenKey);
      if (!token) return;

      // Check token expiration if standard JWT
      const payload = this.decodeJwtPayload(token);
      if (payload && payload.exp && payload.exp * 1000 < Date.now()) {
        await this.logout();
        return;
      }

      this.cachedToken = token;
      const rawUser = await this.secureStorage.getItem(this.userKey);
      let user: LearnerUser | null = null;
      if (rawUser) {
        user = JSON.parse(rawUser);
      } else if (payload && payload.sub) {
        user = {
          id: payload.sub,
          name: payload.name || payload.email || 'Learner',
          email: payload.email,
        };
      }

      if (user) {
        this.currentUser.set(user);
        this.isAuthenticated.set(true);
      }
    } catch (e) {
      console.warn('Error restoring learner auth session:', e);
    }
  }

  /**
   * Safely parses JSON responses from the server, intercepting HTML error pages
   * (e.g. Render spin-up/cold-start 502/503/504 or Cloudflare WAF pages) without crashing.
   */
  private async safeJsonParse<T = any>(
    resp: Response
  ): Promise<{ ok: boolean; status: number; body: T | null; errorMsg?: string }> {
    const contentType = resp.headers?.get?.('content-type') || '';
    if (contentType && !contentType.includes('application/json') && (contentType.includes('text/html') || contentType.includes('text/plain'))) {
      if (resp.status === 502 || resp.status === 503 || resp.status === 504 || resp.status === 429) {
        return {
          ok: false,
          status: resp.status,
          body: null,
          errorMsg: 'The server is currently waking up from standby (free-tier spin-up). Please wait about 20-30 seconds and try again.',
        };
      }
      return {
        ok: false,
        status: resp.status,
        body: null,
        errorMsg: `Server returned unexpected response (status ${resp.status}). Please try again in a moment.`,
      };
    }

    try {
      const body = await resp.json();
      return { ok: resp.ok, status: resp.status, body };
    } catch {
      if (resp.status === 502 || resp.status === 503 || resp.status === 504 || resp.status === 429) {
        return {
          ok: false,
          status: resp.status,
          body: null,
          errorMsg: 'The server is currently waking up from standby (free-tier spin-up). Please wait about 20-30 seconds and try again.',
        };
      }
      return {
        ok: false,
        status: resp.status,
        body: null,
        errorMsg: 'The server is waking up or returned non-JSON data. Please wait a moment and try again.',
      };
    }
  }

  /**
   * Helper to decode payload from JWT without external dependencies.
   */
  private decodeJwtPayload(token: string): any {
    try {
      const parts = token.split('.');
      if (parts.length < 2) return null;
      const base64Url = parts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch {
      return null;
    }
  }

  /**
   * Returns current active Bearer JWT token if authenticated and not expired.
   */
  getToken(): string | null {
    if (!this.cachedToken) {
      // Synchronous fallback read from localStorage on web if not yet cached
      try {
        const token = localStorage.getItem(this.tokenKey);
        if (token) {
          const payload = this.decodeJwtPayload(token);
          if (payload && payload.exp && payload.exp * 1000 < Date.now()) {
            this.logout();
            return null;
          }
          this.cachedToken = token;
        }
      } catch {
        // ignore
      }
    }
    return this.cachedToken;
  }

  /**
   * Stores learner JWT and initializes authenticated session using hardware-backed secure storage.
   */
  setSession(token: string, user?: LearnerUser): void {
    if (!token) return;
    try {
      this.cachedToken = token;
      const decoded = this.decodeJwtPayload(token);
      const profile: LearnerUser = user || {
        id: decoded?.sub || 'learner',
        name: decoded?.name || decoded?.email || 'Learner',
        email: decoded?.email,
      };

      // Store securely without plaintext fallback
      this.secureStorage.setItem(this.tokenKey, token).catch((e) => {
        console.error('Failed to securely store JWT:', e);
      });
      this.secureStorage.setItem(this.userKey, JSON.stringify(profile)).catch((e) => {
        console.error('Failed to securely store user profile:', e);
      });

      this.currentUser.set(profile);
      this.isAuthenticated.set(true);
      this.errorMessage.set(null);
    } catch (e) {
      console.error('Error saving learner session:', e);
    }
  }

  /**
   * Terminate learner session on this device.
   * Clears all in-memory credentials and status. Does NOT wipe anonymous learning progress.
   */
  logout(): void {
    this.cachedToken = null;
    try {
      this.secureStorage.removeItem(this.tokenKey).catch(() => {});
      this.secureStorage.removeItem(this.userKey).catch(() => {});
    } catch (e) {
      console.warn('Error clearing learner session:', e);
    }
    this.isAuthenticated.set(false);
    this.currentUser.set(null);
    this.syncStatus.set('idle');
    this.lastSyncedAt.set(null);
    this.errorMessage.set(null);
  }

  /**
   * Fetches latest progress from the backend.
   */
  async fetchRemoteProgress(): Promise<RemoteLearnerProgress | null> {
    const token = this.getToken();
    if (!token) return null;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/progress'), {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
        signal: controller.signal,
      });

      if (resp.status === 401) {
        this.logout();
        return null;
      }

      if (!resp.ok) {
        throw new Error(`Failed to fetch remote progress (${resp.status})`);
      }

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body?.data) {
        throw new Error(parsed.errorMsg || 'Failed to parse remote progress');
      }
      return parsed.body.data as RemoteLearnerProgress;
    } catch (err: any) {
      const isTimeout = err?.name === 'AbortError';
      const cleanMsg = isTimeout
        ? 'Request timed out while connecting to the server.'
        : 'Network connection unavailable. Changes are saved locally.';
      this.syncStatus.set('error');
      this.errorMessage.set(cleanMsg);
      return null;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Pushes progress payload to backend.
   */
  async pushRemoteProgress(payload: {
    last_lesson: RemoteResumeState | null;
    completed_lesson_ids: string[];
    completed_activity_ids: string[];
    achieved_milestones: RemoteMilestone[];
    client_updated_at?: string;
  }): Promise<RemoteLearnerProgress | null> {
    const token = this.getToken();
    if (!token) return null;

    this.syncStatus.set('syncing');
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/progress'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (resp.status === 401) {
        this.logout();
        return null;
      }

      if (!resp.ok) {
        throw new Error(`Failed to push progress (${resp.status})`);
      }

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body?.data) {
        throw new Error(parsed.errorMsg || 'Failed to push progress');
      }
      this.syncStatus.set('synced');
      this.lastSyncedAt.set(new Date().toISOString());
      this.errorMessage.set(null);
      return parsed.body.data as RemoteLearnerProgress;
    } catch (err: any) {
      const isTimeout = err?.name === 'AbortError';
      const cleanMsg = isTimeout
        ? 'Sync timed out. Progress is safely preserved on this device.'
        : 'Unable to reach the server. Progress is preserved locally on this device.';
      this.syncStatus.set('error');
      this.errorMessage.set(cleanMsg);
      return null;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Register a new learner account (initiates 6-digit email OTP verification).
   */
  async register(
    displayName: string,
    email: string,
    password: string
  ): Promise<{ success: boolean; requires_otp?: boolean; message?: string; token?: string; user?: LearnerUser; error?: string }> {
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/auth/register'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          name: displayName,
          display_name: displayName,
          email,
          password,
        }),
      });

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body) {
        const errorMsg = parsed.errorMsg || 'Registration request could not be completed. Please try again.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const body = parsed.body;
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Registration failed. Please check your details.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      // Check if registration requires OTP challenge (standard secure flow)
      if (payload.requires_otp) {
        return {
          success: true,
          requires_otp: true,
          message: payload.message || 'Verification code sent to your email.',
        };
      }

      // Direct token fallback if OTP unconfigured
      const token = payload.token || body.token;
      const user = payload.user || body.user;
      if (token) {
        this.setSession(token, user);
      }
      return { success: true, token, user };
    } catch (err: any) {
      const errorMsg = err.message || 'Network error during registration.';
      this.errorMessage.set(errorMsg);
      return { success: false, error: errorMsg };
    }
  }

  /**
   * Verify 6-digit OTP code to complete new learner registration.
   */
  async verifySignup(
    email: string,
    otp: string
  ): Promise<{ success: boolean; token?: string; user?: LearnerUser; error?: string }> {
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/auth/verify-signup'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ email, otp }),
      });

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body) {
        const errorMsg = parsed.errorMsg || 'Verification request could not be completed. Please try again.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const body = parsed.body;
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Invalid verification code.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const token = payload.token || body.token;
      const user = payload.user || body.user;
      this.setSession(token, user);
      return { success: true, token, user };
    } catch (err: any) {
      const errorMsg = err.message || 'Network error during verification.';
      this.errorMessage.set(errorMsg);
      return { success: false, error: errorMsg };
    }
  }

  /**
   * Resend a 6-digit OTP code.
   */
  async resendOtp(
    email: string,
    purpose: 'signup' | 'reset_password' = 'signup'
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/auth/resend-otp'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ email, purpose }),
      });

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body) {
        return { success: false, error: parsed.errorMsg || 'Failed to resend code.' };
      }

      const body = parsed.body;
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Failed to resend code.';
        return { success: false, error: errorMsg };
      }

      return {
        success: true,
        message: payload.message || 'A new verification code has been sent to your email.',
      };
    } catch (err: any) {
      return { success: false, error: err.message || 'Network error.' };
    }
  }

  /**
   * Log in to an existing learner account.
   */
  async login(
    email: string,
    password: string
  ): Promise<{ success: boolean; token?: string; user?: LearnerUser; error?: string }> {
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/auth/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body) {
        const errorMsg = parsed.errorMsg || 'Unable to sign in. Please try again.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const body = parsed.body;
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Invalid email or password.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const token = payload.token || body.token;
      const user = payload.user || body.user;
      this.setSession(token, user);
      return { success: true, token, user };
    } catch (err: any) {
      const errorMsg = err.message || 'Network error during login.';
      this.errorMessage.set(errorMsg);
      return { success: false, error: errorMsg };
    }
  }

  /**
   * Request 6-digit OTP code for password recovery.
   */
  async recover(email: string): Promise<{ success: boolean; requires_otp?: boolean; message?: string; error?: string }> {
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/auth/recover'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body) {
        return { success: false, error: parsed.errorMsg || 'Unable to process recovery request.' };
      }

      const body = parsed.body;
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Unable to process recovery request.';
        return { success: false, error: errorMsg };
      }

      return {
        success: true,
        requires_otp: payload.requires_otp ?? true,
        message: payload.message || body.message || 'If an account exists, a 6-digit verification code has been sent.',
      };
    } catch (err: any) {
      return { success: false, error: err.message || 'Network error during recovery.' };
    }
  }

  /**
   * Reset password using verified 6-digit OTP.
   */
  async resetPassword(
    email: string,
    otp: string,
    newPassword: string
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/auth/reset-password'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ email, otp, new_password: newPassword }),
      });

      const parsed = await this.safeJsonParse(resp);
      if (!parsed.ok || !parsed.body) {
        const errorMsg = parsed.errorMsg || 'Failed to reset password.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const body = parsed.body;
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Failed to reset password.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      return {
        success: true,
        message: payload.message || 'Password reset successfully.',
      };
    } catch (err: any) {
      const errorMsg = err.message || 'Network error during password reset.';
      this.errorMessage.set(errorMsg);
      return { success: false, error: errorMsg };
    }
  }
}

