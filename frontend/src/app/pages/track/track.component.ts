import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ConcernService, ConcernTrackingData } from '../../services/concern.service';

@Component({
  selector: 'app-track',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './track.component.html',
  styleUrls: ['./track.component.css'],
})
export class TrackConcernComponent implements OnInit {
  private concernService = inject(ConcernService);
  private route = inject(ActivatedRoute);

  referenceId = signal<string>('');
  trackingToken = signal<string>('');
  loading = signal<boolean>(false);
  errorMessage = signal<string | null>(null);

  reportData = signal<ConcernTrackingData | null>(null);

  // Citizen reply
  replyText = signal<string>('');
  submittingReply = signal<boolean>(false);
  replySuccessMessage = signal<string | null>(null);

  ngOnInit() {
    this.route.queryParams.subscribe((params) => {
      if (params['ref']) {
        this.referenceId.set(params['ref'].trim().toUpperCase());
      }
      if (params['token']) {
        this.trackingToken.set(params['token'].trim());
        this.lookupConcern();
      }
    });
  }

  lookupConcern() {
    this.errorMessage.set(null);
    this.replySuccessMessage.set(null);

    const ref = this.referenceId().trim().toUpperCase();
    const token = this.trackingToken().trim();

    if (!ref || !token) {
      this.errorMessage.set('Both Reference ID and Private Tracking Token are required.');
      return;
    }

    this.loading.set(true);
    this.concernService.trackConcern(ref, token).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.reportData.set(res.data);
      },
      error: (err) => {
        this.loading.set(false);
        const msg = err.error?.error?.message || 'Unable to find a concern matching the provided reference and token.';
        this.errorMessage.set(msg);
      },
    });
  }

  submitCitizenReply() {
    if (!this.replyText().trim()) return;

    this.submittingReply.set(true);
    this.errorMessage.set(null);

    this.concernService
      .replyToConcern(this.referenceId().trim().toUpperCase(), this.trackingToken().trim(), this.replyText().trim())
      .subscribe({
        next: (res) => {
          this.submittingReply.set(false);
          this.replySuccessMessage.set(res.message);
          this.replyText.set('');
          // Refresh report data
          this.lookupConcern();
        },
        error: (err) => {
          this.submittingReply.set(false);
          const msg = err.error?.error?.message || 'Failed to submit reply. Please try again.';
          this.errorMessage.set(msg);
        },
      });
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'received':
        return 'badge-received';
      case 'under_review':
        return 'badge-review';
      case 'assigned':
      case 'action_in_progress':
        return 'badge-progress';
      case 'needs_more_info':
        return 'badge-warning';
      case 'resolved':
      case 'closed':
        return 'badge-resolved';
      case 'rejected':
        return 'badge-rejected';
      default:
        return 'badge-default';
    }
  }
}
