import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, catchError, throwError, shareReplay } from 'rxjs';
import { ApiConfigService } from './api-config.service';
import {
  ApiResponse,
  Topic,
  LessonSummary,
  LessonDetail,
  HealthCheck,
  TopicMasteryChallenge,
} from '../models/api.models';

/**
 * Central HTTP service for all backend API v1 communication.
 *
 * All public methods return the unwrapped `data` payload from the
 * `{ data, meta }` envelope returned by the Flask backend.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly apiConfig = inject(ApiConfigService);
  private topicsCache$?: Observable<Topic[]>;

  private get baseUrl(): string {
    return this.apiConfig.apiBaseUrl;
  }

  constructor(private readonly http: HttpClient) {}

  /** GET /api/v1/topics — list published topics with shared replay caching. */
  getTopics(forceRefresh = false): Observable<Topic[]> {
    if (forceRefresh || !this.topicsCache$) {
      this.topicsCache$ = this.http
        .get<ApiResponse<Topic[]>>(`${this.baseUrl}/topics`)
        .pipe(
          map((res) => res.data),
          catchError((err) => {
            this.topicsCache$ = undefined;
            return this.handleError(err);
          }),
          shareReplay({ bufferSize: 1, refCount: false }),
        );
    }
    return this.topicsCache$;
  }

  /** GET /api/v1/topics/:topicId/lessons — list published lessons for a topic. */
  getTopicLessons(topicId: string): Observable<LessonSummary[]> {
    return this.http
      .get<ApiResponse<LessonSummary[]>>(
        `${this.baseUrl}/topics/${topicId}/lessons`,
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  /** GET /api/v1/topics/:topicId/mastery — get topic mastery challenge. */
  getTopicMastery(topicId: string): Observable<TopicMasteryChallenge> {
    return this.http
      .get<ApiResponse<TopicMasteryChallenge>>(
        `${this.baseUrl}/topics/${topicId}/mastery`,
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  /** GET /api/v1/lessons/:lessonId — get full published lesson detail. */
  getLessonDetail(lessonId: string): Observable<LessonDetail> {
    return this.http
      .get<ApiResponse<LessonDetail>>(
        `${this.baseUrl}/lessons/${lessonId}`,
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  /** GET /api/v1/health — process liveness check. */
  getHealth(): Observable<HealthCheck> {
    return this.http
      .get<ApiResponse<HealthCheck>>(`${this.baseUrl}/health`)
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  /** GET /api/v1/health/ready — process and database readiness probe. */
  getReadiness(): Observable<{ status: string; database?: string }> {
    return this.http
      .get<{ status: string; database?: string }>(`${this.baseUrl}/health/ready`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: unknown): Observable<never> {
    console.error('API request failed:', error);
    return throwError(() => error);
  }
}
