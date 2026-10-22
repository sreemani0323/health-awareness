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

    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/progress'), {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
      });

      if (resp.status === 401) {
        this.logout();
        return null;
      }

      if (!resp.ok) {
        throw new Error(`Failed to fetch remote progress (${resp.status})`);
      }

      const body = await resp.json();
      return body.data as RemoteLearnerProgress;
    } catch (err: any) {
      console.error('Error fetching remote learner progress:', err);
      this.syncStatus.set('error');
      this.errorMessage.set(err.message || 'Network error fetching progress');
      return null;
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
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/learner/progress'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (resp.status === 401) {
        this.logout();
        return null;
      }

      if (!resp.ok) {
        throw new Error(`Failed to push progress (${resp.status})`);
      }

      const body = await resp.json();
      this.syncStatus.set('synced');
      this.lastSyncedAt.set(new Date().toISOString());
      this.errorMessage.set(null);
      return body.data as RemoteLearnerProgress;
    } catch (err: any) {
      console.error('Error pushing remote learner progress:', err);
      this.syncStatus.set('error');
      this.errorMessage.set(err.message || 'Network error saving progress');
      return null;
    }
  }

  /**
   * Register a new learner account.
   */
  async register(
    displayName: string,
    email: string,
    password: string
  ): Promise<{ success: boolean; token?: string; user?: LearnerUser; error?: string }> {
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

      const body = await resp.json();
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Registration failed. Please check your details.';
        this.errorMessage.set(errorMsg);
        return { success: false, error: errorMsg };
      }

      const token = payload.token || body.token;
      const user = payload.user || body.user;
      this.setSession(token, user);
      return { success: true, token, user };
    } catch (err: any) {
      const errorMsg = err.message || 'Network error during registration.';
      this.errorMessage.set(errorMsg);
      return { success: false, error: errorMsg };
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

      const body = await resp.json();
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
   * Request account recovery / password reset instructions.
   */
  async recover(email: string): Promise<{ success: boolean; message?: string; error?: string }> {
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

      const body = await resp.json();
      const payload = body?.data || body;
      if (!resp.ok) {
        const errorMsg = body?.error?.message || payload?.error?.message || 'Unable to process recovery request.';
        return { success: false, error: errorMsg };
      }

      return {
        success: true,
        message: payload.message || body.message || 'If an account exists, instructions have been sent.',
      };
    } catch (err: any) {
      return { success: false, error: err.message || 'Network error during recovery.' };
    }
  }
}

