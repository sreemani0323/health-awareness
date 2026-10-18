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
  activeTab: 'overview' | 'users' | 'content' = 'overview';

  // Data
  overview: AdminOverview | null = null;
  users: AdminUser[] = [];
  topics: AdminTopicRow[] = [];

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
      if (tab === 'users' || tab === 'content' || tab === 'overview') {
        this.activeTab = tab;
      } else {
        this.activeTab = 'overview';
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

  setTab(tab: 'overview' | 'users' | 'content'): void {
    this.activeTab = tab;
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: tab === 'overview' ? null : tab },
      queryParamsHandling: 'merge',
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
