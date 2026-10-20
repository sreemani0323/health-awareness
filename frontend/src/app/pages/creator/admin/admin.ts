import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import {
  AdminUser,
  AdminOverview,
  AuthUser,
  CreatorTopic,
  CreatorLesson,
  StaffApplicationAdminItem,
  StaffApplicationDetail,
  VerificationChecklistData,
} from '../../../models/creator.models';
import { CreatorNavbarComponent } from '../../../components/creator-navbar/creator-navbar.component';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface AdminTopicRow extends CreatorTopic {
  chapterCount: number;
  inReviewCount: number;
}

@Component({
  selector: 'app-admin-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CreatorNavbarComponent],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class AdminWorkspaceComponent implements OnInit {
  currentUser: AuthUser | null = null;
  activeTab: 'overview' | 'users' | 'applications' | 'content' = 'overview';

  // Data
  overview: AdminOverview | null = null;
  users: AdminUser[] = [];
  topics: AdminTopicRow[] = [];

  // Staff Applications Queue (Phase 1B)
  staffApplications: StaffApplicationAdminItem[] = [];
  appStatusFilter = 'all';
  appSearchQuery = '';
  isLoadingApplications = false;

  // Selected Application Detail & Review
  selectedAppDetail: StaffApplicationDetail | null = null;
  isLoadingAppDetail = false;
  isClaimingApp = false;
  isSavingChecklist = false;

  // Decision Modals
  showApproveModal = false;
  approveRole = 'contributor';
  approveJurisdiction = '';
  approveRationale = '';
  isApproving = false;
  provisionedCredentialsResult: {
    username: string;
    temp_setup_password: string;
    approved_role: string;
    reference_id: string;
  } | null = null;
  credentialsCopied = false;

  showRejectModal = false;
  rejectReason = '';
  isRejecting = false;

  showRequestInfoModal = false;
  requestInfoDetails = '';
  isRequestingInfo = false;

  // State
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  // User Filter & Search
  userSearch = '';
  roleFilter = 'all';

  // Create User Modal
  showCreateUserModal = false;
  newUsername = '';
  newDisplayName = '';
  newRole: 'contributor' | 'reviewer' | 'admin' = 'contributor';
  newPassword = '';
  isCreatingUser = false;
  createUserError = '';

  // Change Role Modal
  userForRoleChange: AdminUser | null = null;
  selectedRoleForChange: 'contributor' | 'reviewer' | 'admin' = 'contributor';
  isChangingRole = false;

  // Deactivate/Activate Confirmation Modal
  userForStatusChange: AdminUser | null = null;
  isChangingStatus = false;

  constructor(
    public creatorApi: CreatorApiService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.creatorApi.currentUser$.subscribe((user) => {
      this.currentUser = user;
      if (user && user.role !== 'admin') {
        // Enforce route protection
        this.router.navigate(['/creator']);
      }
      this.cdr.markForCheck();
    });

    this.route.queryParams.subscribe((params) => {
      const tab = params['tab'];
      if (tab === 'users' || tab === 'content' || tab === 'overview' || tab === 'applications') {
        this.activeTab = tab;
      } else {
        this.activeTab = 'overview';
      }
      if (this.activeTab === 'applications') {
        this.loadStaffApplications();
      }
      this.cdr.markForCheck();
    });

    this.loadAdminData();
  }

  loadAdminData(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    forkJoin({
      overview: this.creatorApi.getAdminOverview().pipe(catchError(() => of(null))),
      users: this.creatorApi.getAdminUsers().pipe(catchError(() => of([]))),
      topics: this.creatorApi.getTopics().pipe(catchError(() => of([]))),
    }).subscribe({
      next: ({ overview, users, topics }) => {
        this.overview = overview;
        this.users = users;

        if (topics.length > 0) {
          const lessonRequests = topics.map((t) =>
            this.creatorApi.getTopicLessons(t.id).pipe(catchError(() => of([])))
          );

          forkJoin(lessonRequests).subscribe({
            next: (lessonArrays) => {
              this.topics = topics.map((t, index) => {
                const lessons = lessonArrays[index] || [];
                const inReview = lessons.filter((l) => l.status === 'submitted_for_review').length;
                return {
                  ...t,
                  chapterCount: lessons.length,
                  inReviewCount: inReview,
                };
              });
              this.isLoading = false;
              this.cdr.markForCheck();
            },
            error: () => {
              this.topics = topics.map((t) => ({ ...t, chapterCount: 0, inReviewCount: 0 }));
              this.isLoading = false;
              this.cdr.markForCheck();
            },
          });
        } else {
          this.topics = [];
          this.isLoading = false;
          this.cdr.markForCheck();
        }
      },
      error: (err) => {
        this.isLoading = false;
        if (err?.status === 401 || err?.status === 403) {
          this.router.navigate(['/creator']);
        } else {
          this.errorMessage = 'Failed to load administrative overview. Please refresh.';
        }
        this.cdr.markForCheck();
      },
    });
  }

  setTab(tab: 'overview' | 'users' | 'applications' | 'content'): void {
    this.activeTab = tab;
    if (tab === 'applications' && this.staffApplications.length === 0) {
      this.loadStaffApplications();
    }
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: tab === 'overview' ? null : tab },
      queryParamsHandling: 'merge',
    });
  }

  // --- Staff Applications & Vetting (Phase 1B) ---

  loadStaffApplications(): void {
    this.isLoadingApplications = true;
    this.cdr.markForCheck();

    this.creatorApi
      .getAdminStaffApplications(this.appStatusFilter, this.appSearchQuery)
      .subscribe({
        next: (data) => {
          this.staffApplications = data.applications || [];
          this.isLoadingApplications = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.isLoadingApplications = false;
          this.errorMessage =
            err?.error?.error?.message || 'Failed to load staff applications queue.';
          this.cdr.markForCheck();
        },
      });
  }

  filterStaffApplications(): void {
    this.loadStaffApplications();
  }

  openApplicationDetail(applicationId: string): void {
    this.isLoadingAppDetail = true;
    this.selectedAppDetail = null;
    this.provisionedCredentialsResult = null;
    this.credentialsCopied = false;
    this.cdr.markForCheck();

    this.creatorApi.getAdminStaffApplicationDetail(applicationId).subscribe({
      next: (detail) => {
        this.selectedAppDetail = detail;
        this.isLoadingAppDetail = false;
        // Pre-populate approval role with requested role if valid
        if (['contributor', 'reviewer', 'case_handler', 'jurisdiction_officer'].includes(detail.requested_role)) {
          this.approveRole = detail.requested_role;
        } else {
          this.approveRole = 'contributor';
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.isLoadingAppDetail = false;
        this.errorMessage =
          err?.error?.error?.message || 'Failed to load application detail.';
        this.cdr.markForCheck();
      },
    });
  }

  closeApplicationDetail(): void {
    this.selectedAppDetail = null;
    this.showApproveModal = false;
    this.showRejectModal = false;
    this.showRequestInfoModal = false;
    this.provisionedCredentialsResult = null;
    this.credentialsCopied = false;
  }

  claimApplication(appId: string): void {
    this.isClaimingApp = true;
    this.cdr.markForCheck();

    this.creatorApi.claimStaffApplication(appId).subscribe({
      next: () => {
        this.isClaimingApp = false;
        this.showFlashSuccess('Application review claimed successfully.');
        this.loadStaffApplications();
        if (this.selectedAppDetail) {
          this.openApplicationDetail(appId);
        }
      },
      error: (err) => {
        this.isClaimingApp = false;
        this.errorMessage =
          err?.error?.error?.message || 'Failed to claim application.';
        this.cdr.markForCheck();
      },
    });
  }

  saveVerificationChecklist(): void {
    if (!this.selectedAppDetail) return;

    this.isSavingChecklist = true;
    const detail = this.selectedAppDetail;

    this.creatorApi
      .updateStaffApplicationChecklist(
        detail.application_id,
        detail.verification_checklist,
        detail.internal_notes || '',
      )
      .subscribe({
        next: () => {
          this.isSavingChecklist = false;
          this.showFlashSuccess('Verification checklist and internal notes saved.');
          this.openApplicationDetail(detail.application_id);
        },
        error: (err) => {
          this.isSavingChecklist = false;
          this.errorMessage =
            err?.error?.error?.message || 'Failed to update checklist.';
          this.cdr.markForCheck();
        },
      });
  }

  openApproveModal(): void {
    if (!this.selectedAppDetail) return;
    this.showApproveModal = true;
    this.approveRationale = '';
    this.approveJurisdiction = '';
    this.provisionedCredentialsResult = null;
    this.credentialsCopied = false;
  }

  confirmApprove(): void {
    if (!this.selectedAppDetail) return;
    this.isApproving = true;
    this.cdr.markForCheck();

    const appId = this.selectedAppDetail.application_id;
    this.creatorApi
      .approveStaffApplication(
        appId,
        this.approveRole,
        this.approveJurisdiction.trim() || undefined,
        this.approveRationale.trim() || undefined,
      )
      .subscribe({
        next: (result) => {
          this.isApproving = false;
          this.provisionedCredentialsResult = result;
          this.showFlashSuccess('Application approved and staff account provisioned.');
          this.loadStaffApplications();
          this.openApplicationDetail(appId);
        },
        error: (err) => {
          this.isApproving = false;
          this.errorMessage =
            err?.error?.error?.message || 'Failed to approve application.';
          this.cdr.markForCheck();
        },
      });
  }

  copyProvisionedCredentials(): void {
    if (!this.provisionedCredentialsResult) return;
    const r = this.provisionedCredentialsResult;
    const text = `HealthAware Staff Account Credentials\nReference: ${r.reference_id}\nUsername: ${r.username}\nTemporary Password: ${r.temp_setup_password}\nRole: ${r.approved_role}`;
    navigator.clipboard.writeText(text).then(() => {
      this.credentialsCopied = true;
      this.cdr.markForCheck();
      setTimeout(() => {
        this.credentialsCopied = false;
        this.cdr.markForCheck();
      }, 3000);
    });
  }

  openRejectModal(): void {
    this.showRejectModal = true;
    this.rejectReason = '';
  }

  confirmReject(): void {
    if (!this.selectedAppDetail || !this.rejectReason.trim()) return;
    this.isRejecting = true;
    this.cdr.markForCheck();

    const appId = this.selectedAppDetail.application_id;
    this.creatorApi.rejectStaffApplication(appId, this.rejectReason.trim()).subscribe({
      next: () => {
        this.isRejecting = false;
        this.showRejectModal = false;
        this.showFlashSuccess('Application has been declined.');
        this.loadStaffApplications();
        this.openApplicationDetail(appId);
      },
      error: (err) => {
        this.isRejecting = false;
        this.errorMessage =
          err?.error?.error?.message || 'Failed to reject application.';
        this.cdr.markForCheck();
      },
    });
  }

  openRequestInfoModal(): void {
    this.showRequestInfoModal = true;
    this.requestInfoDetails = '';
  }

  confirmRequestInfo(): void {
    if (!this.selectedAppDetail || !this.requestInfoDetails.trim()) return;
    this.isRequestingInfo = true;
    this.cdr.markForCheck();

    const appId = this.selectedAppDetail.application_id;
    this.creatorApi
      .requestMoreInfoStaffApplication(appId, this.requestInfoDetails.trim())
      .subscribe({
        next: () => {
          this.isRequestingInfo = false;
          this.showRequestInfoModal = false;
          this.showFlashSuccess('Follow-up request sent to applicant.');
          this.loadStaffApplications();
          this.openApplicationDetail(appId);
        },
        error: (err) => {
          this.isRequestingInfo = false;
          this.errorMessage =
            err?.error?.error?.message || 'Failed to request follow-up information.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Filtering & Metrics ---

  get totalUsersCount(): number {
    return this.users.length;
  }

  get activeUsersCount(): number {
    return this.users.filter((u) => u.is_active).length;
  }

  get filteredUsers(): AdminUser[] {
    return this.users.filter((user) => {
      if (this.roleFilter !== 'all' && user.role !== this.roleFilter) {
        return false;
      }
      if (this.userSearch.trim()) {
        const q = this.userSearch.toLowerCase();
        const matchesName = user.display_name?.toLowerCase().includes(q);
        const matchesUser = user.username?.toLowerCase().includes(q);
        if (!matchesName && !matchesUser) {
          return false;
        }
      }
      return true;
    });
  }

  // --- Create User Modal ---

  openCreateUserModal(): void {
    this.newUsername = '';
    this.newDisplayName = '';
    this.newRole = 'contributor';
    this.newPassword = '';
    this.createUserError = '';
    this.showCreateUserModal = true;
  }

  closeCreateUserModal(): void {
    this.showCreateUserModal = false;
    this.createUserError = '';
  }

  submitCreateUser(): void {
    if (!this.newUsername.trim() || !this.newDisplayName.trim() || !this.newPassword.trim()) {
      this.createUserError = 'Please fill out all required fields.';
      return;
    }
    if (this.newPassword.length < 8) {
      this.createUserError = 'Password must be at least 8 characters long.';
      return;
    }

    this.isCreatingUser = true;
    this.createUserError = '';
    this.cdr.markForCheck();

    this.creatorApi
      .createAdminUser({
        username: this.newUsername.trim(),
        display_name: this.newDisplayName.trim(),
        role: this.newRole,
        password: this.newPassword.trim(),
      })
      .subscribe({
        next: (created) => {
          this.users.push(created);
          this.isCreatingUser = false;
          this.showCreateUserModal = false;
          this.showFlashSuccess(`Account "${created.username}" created successfully.`);
          if (this.overview) {
            this.overview.total_users += 1;
            this.overview.active_users += 1;
            this.overview.users_by_role[created.role] += 1;
          }
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.isCreatingUser = false;
          this.createUserError =
            err?.error?.error?.message || 'Failed to create user. Ensure username is unique.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Role Change ---

  openChangeRoleModal(user: AdminUser): void {
    this.userForRoleChange = user;
    this.selectedRoleForChange = user.role;
  }

  closeChangeRoleModal(): void {
    this.userForRoleChange = null;
  }

  confirmChangeRole(): void {
    if (!this.userForRoleChange) return;

    this.isChangingRole = true;
    const target = this.userForRoleChange;
    const newRole = this.selectedRoleForChange;

    this.creatorApi.updateAdminUserRole(target.user_id, newRole).subscribe({
      next: (updated) => {
        target.role = updated.role;
        this.isChangingRole = false;
        this.userForRoleChange = null;
        this.showFlashSuccess(`Role for "${target.username}" changed to ${updated.role}.`);
        if (this.overview) {
          this.loadAdminData(); // Refresh summary metrics
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.isChangingRole = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to change role.';
        this.cdr.markForCheck();
      },
    });
  }

  // --- Deactivation / Activation ---

  openStatusChangeModal(user: AdminUser): void {
    this.userForStatusChange = user;
  }

  closeStatusChangeModal(): void {
    this.userForStatusChange = null;
  }

  confirmStatusChange(): void {
    if (!this.userForStatusChange) return;

    this.isChangingStatus = true;
    const target = this.userForStatusChange;
    const newStatus = !target.is_active;

    this.creatorApi.setAdminUserStatus(target.user_id, newStatus).subscribe({
      next: (updated) => {
        target.is_active = updated.is_active;
        this.isChangingStatus = false;
        this.userForStatusChange = null;
        const actionVerb = updated.is_active ? 'activated' : 'deactivated';
        this.showFlashSuccess(`Account "${target.username}" was successfully ${actionVerb}.`);
        if (this.overview) {
          if (updated.is_active) {
            this.overview.active_users += 1;
            this.overview.deactivated_users -= 1;
          } else {
            this.overview.active_users -= 1;
            this.overview.deactivated_users += 1;
          }
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.isChangingStatus = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to update account status.';
        this.userForStatusChange = null;
        this.cdr.markForCheck();
      },
    });
  }

  private showFlashSuccess(msg: string): void {
    this.successMessage = msg;
    this.cdr.markForCheck();
    setTimeout(() => {
      this.successMessage = '';
      this.cdr.markForCheck();
    }, 4000);
  }
}
