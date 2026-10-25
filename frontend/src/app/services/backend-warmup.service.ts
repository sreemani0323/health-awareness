import { Injectable, inject, signal } from '@angular/core';
import { Observable, of, tap, catchError, timeout, map } from 'rxjs';
import { ApiService } from './api.service';

export interface WarmupResult {
  ready: boolean;
  database: string;
  topicsPrefetched: boolean;
  error?: string;
}

@Injectable({ providedIn: 'root' })
export class BackendWarmupService {
  private readonly api = inject(ApiService);

  readonly isWarming = signal<boolean>(false);
  readonly isReady = signal<boolean>(false);
  readonly warmupError = signal<string | null>(null);

  private warmupInFlight$?: Observable<WarmupResult>;
  private hasCompleted = false;

  /**
   * Initiates a lightweight, non-blocking backend startup probe.
   * Checks /api/v1/health/ready and concurrently warms the public curriculum cache.
   * Safe across Web and Native Android. Does not block initial page rendering.
   */
  warmup(): Observable<WarmupResult> {
    if (this.hasCompleted && this.isReady()) {
      return of({
        ready: true,
        database: 'connected',
        topicsPrefetched: true,
      });
    }

    if (this.warmupInFlight$) {
      return this.warmupInFlight$;
    }

    this.isWarming.set(true);
    this.warmupError.set(null);

    this.warmupInFlight$ = this.api.getReadiness().pipe(
      timeout(6000),
      tap((res) => {
        this.isReady.set(res?.status === 'ready');
        // Concurrently prefetch public curriculum metadata without blocking
        this.api.getTopics().subscribe({
          error: (err) => console.warn('Curriculum metadata prefetch deferred:', err),
        });
      }),
      map((res) => ({
        ready: res?.status === 'ready',
        database: res?.database || 'unknown',
        topicsPrefetched: true,
      })),
      catchError((err) => {
        console.warn('Backend warmup check returned degraded state (non-fatal):', err);
        const errMsg = err?.message || 'Backend is starting up or temporarily unreachable.';
        this.warmupError.set(errMsg);
        this.isReady.set(false);
        return of({
          ready: false,
          database: 'disconnected',
          topicsPrefetched: false,
          error: errMsg,
        });
      }),
      tap(() => {
        this.isWarming.set(false);
        this.hasCompleted = true;
        this.warmupInFlight$ = undefined;
      }),
    );

    return this.warmupInFlight$;
  }

  /** Explicit retry when network reconnects or user triggers refresh. */
  retry(): Observable<WarmupResult> {
    this.hasCompleted = false;
    this.warmupInFlight$ = undefined;
    return this.warmup();
  }
}
