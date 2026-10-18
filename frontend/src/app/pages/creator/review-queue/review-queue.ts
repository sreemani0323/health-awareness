import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import { CreatorVersion, AuthUser } from '../../../models/creator.models';
import { CreatorNavbarComponent } from '../../../components/creator-navbar/creator-navbar.component';

@Component({
  selector: 'ha-review-queue',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CreatorNavbarComponent],
  templateUrl: './review-queue.html',
  styleUrl: './review-queue.css',
})
export class ReviewQueue implements OnInit {
  items: CreatorVersion[] = [];
  currentUser: AuthUser | null = null;
  isLoading = true;
  errorMessage = '';
  successMessage = '';

  // Inspection modal
  inspectedVersion: CreatorVersion | null = null;

  // Changes request modal state
  showChangeNotesModal = false;
  versionForChanges: CreatorVersion | null = null;
  changeNotes = '';

  // Approve modal state
  showApproveModal = false;
  versionToApprove: CreatorVersion | null = null;

  isSubmittingDecision = false;

  constructor(
    public creatorApi: CreatorApiService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.creatorApi.currentUser$.subscribe((user) => {
      this.currentUser = user;
      this.cdr.markForCheck();
    });
    this.loadQueue();
  }

  loadQueue(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.getReviewQueue().subscribe({
      next: (versions) => {
        this.items = versions;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        if (err?.status === 401) {
          this.router.navigate(['/creator/login']);
          return;
        }
        this.errorMessage =
          err?.error?.error?.message || 'Access restricted. Review Queue is available only to accredited Reviewers and Administrators.';
        this.isLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  // --- Inspection Drawer/Modal ---

  inspectVersion(version: CreatorVersion): void {
    this.inspectedVersion = version;
    this.cdr.markForCheck();
  }

  closeInspect(): void {
    this.inspectedVersion = null;
  }

  // --- Approval Modal ---

  openApproveModal(version: CreatorVersion): void {
    this.versionToApprove = version;
    this.showApproveModal = true;
    this.errorMessage = '';
  }

  closeApproveModal(): void {
    this.showApproveModal = false;
    this.versionToApprove = null;
  }

  confirmApprove(): void {
    if (!this.versionToApprove) return;

    this.isSubmittingDecision = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.cdr.markForCheck();

    const versionId = this.versionToApprove.id;
    const title = this.versionToApprove.title;
    this.creatorApi.approveVersion(versionId).subscribe({
      next: () => {
        this.successMessage = `Successfully approved and published "${title}". It is now live in public learner curriculum!`;
        this.isSubmittingDecision = false;
        this.showApproveModal = false;
        this.versionToApprove = null;
        if (this.inspectedVersion?.id === versionId) {
          this.inspectedVersion = null;
        }
        this.cdr.markForCheck();
        this.loadQueue();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error?.message || 'Failed to approve version. Notice: Self-approval is strictly forbidden.';
        this.isSubmittingDecision = false;
        this.cdr.markForCheck();
      },
    });
  }

  // --- Request Changes Modal ---

  openChangeNotes(version: CreatorVersion): void {
    this.versionForChanges = version;
    this.changeNotes = '';
    this.showChangeNotesModal = true;
    this.errorMessage = '';
    this.cdr.markForCheck();
  }

  closeChangeNotesModal(): void {
    this.showChangeNotesModal = false;
    this.versionForChanges = null;
    this.changeNotes = '';
  }

  submitChangeNotes(): void {
    if (!this.versionForChanges) return;
    if (!this.changeNotes.trim()) {
      this.errorMessage = 'Please provide constructive, specific feedback explaining why changes are requested.';
      return;
    }

    this.isSubmittingDecision = true;
    const versionId = this.versionForChanges.id;
    const title = this.versionForChanges.title;
    this.cdr.markForCheck();

    this.creatorApi.requestChanges(versionId, this.changeNotes.trim()).subscribe({
      next: () => {
        this.successMessage = `Feedback sent for "${title}". The chapter has been reverted to draft status for author revision.`;
        this.showChangeNotesModal = false;
        this.versionForChanges = null;
        this.changeNotes = '';
        this.isSubmittingDecision = false;
        if (this.inspectedVersion?.id === versionId) {
          this.inspectedVersion = null;
        }
        this.cdr.markForCheck();
        this.loadQueue();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error?.message || 'Failed to request changes.';
        this.isSubmittingDecision = false;
        this.cdr.markForCheck();
      },
    });
  }
}
