import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, catchError, throwError, BehaviorSubject, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { ApiResponse } from '../models/api.models';
import {
  AuthUser,
  CreatorTopic,
  CreatorLesson,
  CreatorVersion,
  CreatorSource,
  LoginRequest,
  AdminUser,
  AdminOverview,
  CreateUserRequest,
  PublicStaffApplicationSubmitRequest,
  PublicStaffApplicationView,
  StaffApplicationAdminItem,
  StaffApplicationDetail,
  VerificationChecklistData,
} from '../models/creator.models';

/**
 * HTTP service for Creator Studio API endpoints.
 * Handles auth state and all creator CRUD + workflow operations.
 */
@Injectable({ providedIn: 'root' })
export class CreatorApiService {
  private readonly baseUrl = environment.apiBaseUrl;
  private currentUserSubject = new BehaviorSubject<AuthUser | null>(null);
  currentUser$ = this.currentUserSubject.asObservable();

  constructor(private readonly http: HttpClient) {
    // Check if already authenticated on service init
    this.checkAuth();
  }

  get isAuthenticated(): boolean {
    return this.currentUserSubject.value !== null;
  }

  get currentUser(): AuthUser | null {
    return this.currentUserSubject.value;
  }

  // --- Auth ---

  login(credentials: LoginRequest): Observable<AuthUser> {
    return this.http
      .post<ApiResponse<AuthUser>>(`${this.baseUrl}/auth/login`, credentials, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        tap((user) => this.currentUserSubject.next(user)),
        catchError(this.handleError),
      );
  }

  logout(): Observable<any> {
    return this.http
      .post<ApiResponse<any>>(`${this.baseUrl}/auth/logout`, {}, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        tap(() => this.currentUserSubject.next(null)),
        catchError(this.handleError),
      );
  }

  checkAuth(): void {
    this.http
      .get<ApiResponse<AuthUser>>(`${this.baseUrl}/auth/me`, {
        withCredentials: true,
      })
      .subscribe({
        next: (res) => this.currentUserSubject.next(res.data),
        error: () => this.currentUserSubject.next(null),
      });
  }

  // --- Topics ---

  getTopics(): Observable<CreatorTopic[]> {
    return this.http
      .get<ApiResponse<CreatorTopic[]>>(`${this.baseUrl}/creator/topics`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  getTopic(topicId: string): Observable<CreatorTopic> {
    return this.http
      .get<ApiResponse<CreatorTopic>>(`${this.baseUrl}/creator/topics/${topicId}`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  createTopic(topic: Partial<CreatorTopic>): Observable<CreatorTopic> {
    return this.http
      .post<ApiResponse<CreatorTopic>>(`${this.baseUrl}/creator/topics`, topic, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  updateTopic(topicId: string, topic: Partial<CreatorTopic>): Observable<CreatorTopic> {
    return this.http
      .put<ApiResponse<CreatorTopic>>(`${this.baseUrl}/creator/topics/${topicId}`, topic, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  // --- Lessons ---

  getTopicLessons(topicId: string): Observable<CreatorLesson[]> {
    return this.http
      .get<ApiResponse<CreatorLesson[]>>(`${this.baseUrl}/creator/topics/${topicId}/lessons`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  getLesson(lessonId: string): Observable<CreatorLesson> {
    return this.http
      .get<ApiResponse<CreatorLesson>>(`${this.baseUrl}/creator/lessons/${lessonId}`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  createLesson(topicId: string, lesson: Partial<CreatorLesson> & { title?: string; summary?: string }): Observable<CreatorLesson> {
    return this.http
      .post<ApiResponse<CreatorLesson>>(`${this.baseUrl}/creator/topics/${topicId}/lessons`, lesson, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  updateLesson(lessonId: string, lesson: Partial<CreatorLesson>): Observable<CreatorLesson> {
    return this.http
      .put<ApiResponse<CreatorLesson>>(`${this.baseUrl}/creator/lessons/${lessonId}`, lesson, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  deleteLesson(lessonId: string): Observable<{ deleted: boolean; message: string }> {
    return this.http
      .delete<ApiResponse<{ deleted: boolean; message: string }>>(`${this.baseUrl}/creator/lessons/${lessonId}`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  // --- Versions ---

  getVersions(lessonId: string): Observable<CreatorVersion[]> {
    return this.http
      .get<ApiResponse<CreatorVersion[]>>(`${this.baseUrl}/creator/lessons/${lessonId}/versions`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  createVersion(lessonId: string, version: Partial<CreatorVersion>): Observable<CreatorVersion> {
    return this.http
      .post<ApiResponse<CreatorVersion>>(`${this.baseUrl}/creator/lessons/${lessonId}/versions`, version, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  getVersion(versionId: string): Observable<CreatorVersion> {
    return this.http
      .get<ApiResponse<CreatorVersion>>(`${this.baseUrl}/creator/versions/${versionId}`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  updateVersion(versionId: string, version: Partial<CreatorVersion>): Observable<CreatorVersion> {
    return this.http
      .put<ApiResponse<CreatorVersion>>(`${this.baseUrl}/creator/versions/${versionId}`, version, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  submitForReview(versionId: string): Observable<CreatorVersion> {
    return this.http
      .post<ApiResponse<CreatorVersion>>(`${this.baseUrl}/creator/versions/${versionId}/submit`, {}, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  approveVersion(versionId: string): Observable<CreatorVersion> {
    return this.http
      .post<ApiResponse<CreatorVersion>>(`${this.baseUrl}/creator/versions/${versionId}/approve`, {}, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  requestChanges(versionId: string, notes: string): Observable<CreatorVersion> {
    return this.http
      .post<ApiResponse<CreatorVersion>>(`${this.baseUrl}/creator/versions/${versionId}/request-changes`, { notes }, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  // --- Review Queue ---

  getReviewQueue(): Observable<CreatorVersion[]> {
    return this.http
      .get<ApiResponse<CreatorVersion[]>>(`${this.baseUrl}/creator/reviews`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  // --- Sources ---

  getSources(): Observable<CreatorSource[]> {
    return this.http
      .get<ApiResponse<CreatorSource[]>>(`${this.baseUrl}/creator/sources`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  createSource(source: Partial<CreatorSource>): Observable<CreatorSource> {
    return this.http
      .post<ApiResponse<CreatorSource>>(`${this.baseUrl}/creator/sources`, source, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  // --- Admin User Management & Overview ---

  getAdminUsers(): Observable<AdminUser[]> {
    return this.http
      .get<ApiResponse<AdminUser[]>>(`${this.baseUrl}/admin/users`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  createAdminUser(user: CreateUserRequest): Observable<AdminUser> {
    return this.http
      .post<ApiResponse<AdminUser>>(`${this.baseUrl}/admin/users`, user, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  updateAdminUserRole(userId: string, role: string): Observable<AdminUser> {
    return this.http
      .put<ApiResponse<AdminUser>>(
        `${this.baseUrl}/admin/users/${userId}/role`,
        { role },
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  setAdminUserStatus(userId: string, isActive: boolean): Observable<AdminUser> {
    return this.http
      .put<ApiResponse<AdminUser>>(
        `${this.baseUrl}/admin/users/${userId}/status`,
        { is_active: isActive },
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  getAdminOverview(): Observable<AdminOverview> {
    return this.http
      .get<ApiResponse<AdminOverview>>(`${this.baseUrl}/admin/overview`, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  // --- Staff Applications & Vetting (Phase 1B) ---

  submitStaffApplication(
    req: PublicStaffApplicationSubmitRequest,
  ): Observable<{ reference_id: string; tracking_token: string; status: string; message: string }> {
    return this.http
      .post<ApiResponse<{ reference_id: string; tracking_token: string; status: string; message: string }>>(
        `${this.baseUrl}/staff/apply`,
        req,
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  trackStaffApplication(
    referenceId: string,
    trackingToken: string,
  ): Observable<PublicStaffApplicationView> {
    return this.http
      .post<ApiResponse<PublicStaffApplicationView>>(
        `${this.baseUrl}/staff/applications/track`,
        { reference_id: referenceId, tracking_token: trackingToken },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  respondToStaffApplication(
    referenceId: string,
    trackingToken: string,
    notes: string,
  ): Observable<{ reference_id: string; status: string; message: string }> {
    return this.http
      .post<ApiResponse<{ reference_id: string; status: string; message: string }>>(
        `${this.baseUrl}/staff/applications/${referenceId}/respond`,
        { tracking_token: trackingToken, applicant_notes: notes },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  withdrawStaffApplication(
    referenceId: string,
    trackingToken: string,
    rationale?: string,
  ): Observable<{ reference_id: string; status: string; message: string }> {
    return this.http
      .post<ApiResponse<{ reference_id: string; status: string; message: string }>>(
        `${this.baseUrl}/staff/applications/${referenceId}/withdraw`,
        { tracking_token: trackingToken, rationale },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  getAdminStaffApplications(
    statusFilter?: string,
    searchQuery?: string,
  ): Observable<{ applications: StaffApplicationAdminItem[]; total: number }> {
    let url = `${this.baseUrl}/admin/staff-applications?`;
    if (statusFilter && statusFilter !== 'all') {
      url += `status=${encodeURIComponent(statusFilter)}&`;
    }
    if (searchQuery) {
      url += `q=${encodeURIComponent(searchQuery)}&`;
    }
    return this.http
      .get<ApiResponse<{ applications: StaffApplicationAdminItem[]; total: number }>>(url, {
        withCredentials: true,
      })
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  getAdminStaffApplicationDetail(
    applicationId: string,
  ): Observable<StaffApplicationDetail> {
    return this.http
      .get<ApiResponse<StaffApplicationDetail>>(
        `${this.baseUrl}/admin/staff-applications/${applicationId}`,
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  claimStaffApplication(applicationId: string): Observable<any> {
    return this.http
      .post<ApiResponse<any>>(
        `${this.baseUrl}/admin/staff-applications/${applicationId}/claim`,
        {},
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  updateStaffApplicationChecklist(
    applicationId: string,
    checklist: VerificationChecklistData,
    internalNotes?: string,
  ): Observable<any> {
    return this.http
      .post<ApiResponse<any>>(
        `${this.baseUrl}/admin/staff-applications/${applicationId}/checklist`,
        { verification_checklist: checklist, internal_notes: internalNotes },
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  requestMoreInfoStaffApplication(
    applicationId: string,
    details: string,
  ): Observable<any> {
    return this.http
      .post<ApiResponse<any>>(
        `${this.baseUrl}/admin/staff-applications/${applicationId}/request-info`,
        { details },
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  approveStaffApplication(
    applicationId: string,
    approvedRole: string,
    assignedJurisdiction?: string,
    rationale?: string,
  ): Observable<{
    application_id: string;
    reference_id: string;
    status: string;
    approved_role: string;
    provisioned_user_id: string;
    username: string;
    temp_setup_password: string;
    message: string;
  }> {
    return this.http
      .post<
        ApiResponse<{
          application_id: string;
          reference_id: string;
          status: string;
          approved_role: string;
          provisioned_user_id: string;
          username: string;
          temp_setup_password: string;
          message: string;
        }>
      >(
        `${this.baseUrl}/admin/staff-applications/${applicationId}/approve`,
        {
          approved_role: approvedRole,
          assigned_jurisdiction: assignedJurisdiction,
          rationale,
        },
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  rejectStaffApplication(
    applicationId: string,
    reason: string,
  ): Observable<any> {
    return this.http
      .post<ApiResponse<any>>(
        `${this.baseUrl}/admin/staff-applications/${applicationId}/reject`,
        { reason },
        { withCredentials: true },
      )
      .pipe(
        map((res) => res.data),
        catchError(this.handleError),
      );
  }

  private handleError(error: unknown): Observable<never> {
    console.error('Creator API request failed:', error);
    return throwError(() => error);
  }
}
