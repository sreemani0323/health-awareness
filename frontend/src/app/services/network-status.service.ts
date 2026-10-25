import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiConfigService } from './api-config.service';
import { firstValueFrom } from 'rxjs';
import { BYPASS_RETRY, REQUEST_TIMEOUT_MS } from '../interceptors/api-timeout-retry.interceptor';
import { HttpContext } from '@angular/common/http';

export type ConnectionState = 'online' | 'offline' | 'degraded';

@Injectable({ providedIn: 'root' })
export class NetworkStatusService {
  private readonly http = inject(HttpClient);
  private readonly apiConfig = inject(ApiConfigService);

  private readonly onlineSignal = signal<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  private readonly degradedSignal = signal<boolean>(false);
  private readonly pendingSyncCountSignal = signal<number>(0);

  readonly isOnline = this.onlineSignal.asReadonly();
  readonly isDegraded = this.degradedSignal.asReadonly();
  readonly pendingSyncCount = this.pendingSyncCountSignal.asReadonly();

  readonly connectionStatus = computed<ConnectionState>(() => {
    if (!this.onlineSignal()) {
      return 'offline';
    }
    if (this.degradedSignal()) {
      return 'degraded';
    }
    return 'online';
  });

  private reconnectHandlers: Array<() => Promise<void> | void> = [];

  constructor() {
    this.initNetworkListeners();
  }

  private initNetworkListeners(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      this.handleOnlineEvent();
    });

    window.addEventListener('offline', () => {
      this.handleOfflineEvent();
    });
  }

  /**
   * Called when browser or Capacitor webview detects network connectivity restored.
   */
  async handleOnlineEvent(): Promise<void> {
    this.onlineSignal.set(true);
    // When returning online, verify backend reachability
    const isReachable = await this.checkReachability();
    if (isReachable) {
      this.degradedSignal.set(false);
      // Trigger queued reconnect callbacks (such as offline progress sync)
      this.triggerReconnectHandlers();
    } else {
      this.degradedSignal.set(true);
    }
  }

  /**
   * Called when network connectivity is lost.
   */
  handleOfflineEvent(): void {
    this.onlineSignal.set(false);
    this.degradedSignal.set(false);
  }

  /**
   * Registers a callback to execute automatically when connectivity is restored.
   */
  onReconnect(handler: () => Promise<void> | void): () => void {
    this.reconnectHandlers.push(handler);
    return () => {
      this.reconnectHandlers = this.reconnectHandlers.filter((h) => h !== handler);
    };
  }

  private triggerReconnectHandlers(): void {
    for (const handler of this.reconnectHandlers) {
      try {
        const result = handler();
        if (result instanceof Promise) {
          result.catch((err) => console.warn('Reconnect handler failed:', err));
        }
      } catch (err) {
        console.warn('Error in reconnect handler:', err);
      }
    }
  }

  /**
   * Checks if the HealthAware backend is reachable via a bounded /api/v1/health probe.
   */
  async checkReachability(): Promise<boolean> {
    try {
      const context = new HttpContext()
        .set(REQUEST_TIMEOUT_MS, 4000)
        .set(BYPASS_RETRY, true);

      await firstValueFrom(
        this.http.get<{ data?: { status: string } }>(
          `${this.apiConfig.apiBaseUrl}/health`,
          { context }
        )
      );
      this.degradedSignal.set(false);
      return true;
    } catch {
      if (this.onlineSignal()) {
        this.degradedSignal.set(true);
      }
      return false;
    }
  }

  /**
   * Manually sets degraded state (e.g. when 503 or 502 responses are encountered by interceptor or services).
   */
  setDegraded(degraded: boolean): void {
    this.degradedSignal.set(degraded);
  }

  /**
   * Updates count of pending unsynced local progress operations.
   */
  setPendingSyncCount(count: number): void {
    this.pendingSyncCountSignal.set(Math.max(0, count));
  }
}
