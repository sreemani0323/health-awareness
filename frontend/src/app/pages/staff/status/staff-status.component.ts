import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import { ApiConfigService } from '../../../services/api-config.service';
import { PublicStaffApplicationView } from '../../../models/creator.models';

@Component({
  selector: 'app-staff-status',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './staff-status.component.html',
  styleUrls: ['./staff-status.component.css'],
})
export class StaffStatusComponent implements OnInit {
  private creatorApi = inject(CreatorApiService);
  private apiConfig = inject(ApiConfigService);
  private route = inject(ActivatedRoute);

  // Search state
  referenceId = signal<string>('');
  trackingToken = signal<string>('');
  isLoading = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);

  // Loaded application
  application = signal<PublicStaffApplicationView | null>(null);

  // Follow-up response state
  responseNotes = signal<string>('');
  submittingResponse = signal<boolean>(false);

  // Withdraw state
  showWithdrawModal = signal<boolean>(false);
  withdrawRationale = signal<string>('');
  submittingWithdraw = signal<boolean>(false);

  // Recovery state
  showRecoverModal = signal<boolean>(false);
  recoveryEmail = signal<string>('');
  isRecovering = signal<boolean>(false);

  async recoverApplication(): Promise<void> {
    const email = this.recoveryEmail().trim();
    if (!email || !email.includes('@')) {
      this.errorMessage.set('Please enter a valid email address.');
      return;
    }

    this.isRecovering.set(true);
    this.errorMessage.set(null);
    try {
      const resp = await fetch(this.apiConfig.getApiUrl('/staff/applications/recover'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await resp.json().catch(() => ({}));
      this.isRecovering.set(false);
      this.showRecoverModal.set(false);
      this.recoveryEmail.set('');

      if (resp.ok) {
        this.successMessage.set(
          data.message || 'If an active staff application exists for this email address, tracking recovery instructions have been sent.'
        );
      } else {
        const errorMsg = data.error?.message || 'Unable to process recovery request. Please try again.';
        this.errorMessage.set(errorMsg);
      }
    } catch {
      this.isRecovering.set(false);
      this.errorMessage.set('Network error during recovery request.');
    }
  }


  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      const ref = params['ref'];
      const token = params['token'];
      if (ref && token) {
        this.referenceId.set(ref);
        this.trackingToken.set(token);
        this.trackApplication();
      }
    });
  }

  trackApplication(): void {
    const ref = this.referenceId().trim();
    const token = this.trackingToken().trim();

    if (!ref || !token) {
      this.errorMessage.set('Both Reference ID and Tracking Token are required.');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    this.creatorApi.trackStaffApplication(ref, token).subscribe({
      next: (data) => {
        this.isLoading.set(false);
        this.application.set(data);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.application.set(null);
        const errObj = err.error?.error || err.error || {};
        const msg = errObj.message || 'Unable to find application with these tracking credentials.';
        this.errorMessage.set(msg);
      },
    });
  }

  submitResponse(): void {
    const app = this.application();
    const notes = this.responseNotes().trim();
    const token = this.trackingToken().trim();

    if (!app || !notes) {
      return;
    }

    this.submittingResponse.set(true);
    this.errorMessage.set(null);

    this.creatorApi.respondToStaffApplication(app.reference_id, token, notes).subscribe({
      next: (res) => {
        this.submittingResponse.set(false);
        this.responseNotes.set('');
        this.successMessage.set('Follow-up information submitted successfully. Your application is back under review.');
        this.trackApplication();
      },
      error: (err) => {
        this.submittingResponse.set(false);
        const errObj = err.error?.error || err.error || {};
        const msg = errObj.message || 'Failed to submit response. Please try again.';
        this.errorMessage.set(msg);
      },
    });
  }

  confirmWithdraw(): void {
    const app = this.application();
    const token = this.trackingToken().trim();
    if (!app) return;

    this.submittingWithdraw.set(true);
    this.errorMessage.set(null);

    this.creatorApi.withdrawStaffApplication(app.reference_id, token, this.withdrawRationale().trim() || undefined).subscribe({
      next: () => {
        this.submittingWithdraw.set(false);
        this.showWithdrawModal.set(false);
        this.successMessage.set('Your application has been voluntarily withdrawn.');
        this.trackApplication();
      },
      error: (err) => {
        this.submittingWithdraw.set(false);
        const errObj = err.error?.error || err.error || {};
        this.errorMessage.set(errObj.message || 'Failed to withdraw application.');
      },
    });
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'pending_review': return 'status-pending';
      case 'under_review': return 'status-review';
      case 'more_info_requested': return 'status-info';
      case 'approved': return 'status-approved';
      case 'rejected': return 'status-rejected';
      case 'withdrawn': return 'status-withdrawn';
      default: return 'status-default';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'pending_review': return 'Pending Initial Review';
      case 'under_review': return 'Under Review by Verification Team';
      case 'more_info_requested': return 'Additional Information Requested';
      case 'approved': return 'Approved — Account Provisioned';
      case 'rejected': return 'Application Declined';
      case 'withdrawn': return 'Withdrawn by Applicant';
      default: return status;
    }
  }

  canWithdraw(status?: string): boolean {
    return status === 'pending_review' || status === 'under_review' || status === 'more_info_requested';
  }
}
