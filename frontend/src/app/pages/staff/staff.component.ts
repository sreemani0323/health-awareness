import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ConcernService, StaffMeResponse } from '../../services/concern.service';

@Component({
  selector: 'app-staff',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './staff.component.html',
  styleUrls: ['./staff.component.css'],
})
export class StaffDashboardComponent implements OnInit {
  private concernService = inject(ConcernService);
  private router = inject(Router);

  // Profile & Role
  currentUser = signal<StaffMeResponse['data'] | null>(null);
  loadingUser = signal<boolean>(true);
  unauthorized = signal<boolean>(false);

  // Concerns list
  concerns = signal<any[]>([]);
  loadingConcerns = signal<boolean>(false);
  errorMessage = signal<string | null>(null);

  // Filters
  filterStatus = signal<string>('');
  filterCategory = signal<string>('');
  filterDistrict = signal<string>('');

  // Selected Detail
  selectedConcern = signal<any | null>(null);
  loadingDetail = signal<boolean>(false);

  // Action form state
  newStatus = signal<string>('');
  publicNotes = signal<string>('');
  internalNotes = signal<string>('');
  rejectionReason = signal<string>('');
  resolutionNotes = signal<string>('');
  citizenReplyRequested = signal<boolean>(false);
  actionSubmitting = signal<boolean>(false);
  actionMessage = signal<string | null>(null);

  // Assignment
  handlersList = signal<any[]>([]);
  selectedHandlerId = signal<string>('');

  ngOnInit() {
    this.loadStaffProfile();
  }

  loadStaffProfile() {
    this.loadingUser.set(true);
    this.concernService.getStaffMe().subscribe({
      next: (res) => {
        this.currentUser.set(res.data);
        this.loadingUser.set(false);
        this.unauthorized.set(false);
        this.loadConcerns();
        this.loadHandlers();
      },
      error: () => {
        this.loadingUser.set(false);
        this.unauthorized.set(true);
      },
    });
  }

  loadConcerns() {
    this.loadingConcerns.set(true);
    this.errorMessage.set(null);

    this.concernService
      .getStaffConcerns({
        status: this.filterStatus() || undefined,
        category: this.filterCategory() || undefined,
        district: this.filterDistrict().trim() || undefined,
      })
      .subscribe({
        next: (res) => {
          this.concerns.set(res.data);
          this.loadingConcerns.set(false);
        },
        error: (err) => {
          this.loadingConcerns.set(false);
          this.errorMessage.set('Failed to load concerns list.');
        },
      });
  }

  loadHandlers() {
    this.concernService.getStaffHandlers().subscribe({
      next: (res) => this.handlersList.set(res.data),
      error: () => {},
    });
  }

  openConcernDetail(reportId: string) {
    this.loadingDetail.set(true);
    this.actionMessage.set(null);
    this.errorMessage.set(null);

    this.concernService.getStaffConcernDetail(reportId).subscribe({
      next: (res) => {
        this.selectedConcern.set(res.data);
        this.newStatus.set(res.data.status);
        this.citizenReplyRequested.set(res.data.citizen_reply_requested);
        this.publicNotes.set('');
        this.internalNotes.set('');
        this.rejectionReason.set(res.data.rejection_reason || '');
        this.resolutionNotes.set(res.data.resolution_notes || '');
        this.selectedHandlerId.set(res.data.assigned_handler_id || '');
        this.loadingDetail.set(false);
      },
      error: (err) => {
        this.loadingDetail.set(false);
        this.errorMessage.set('Failed to load concern details.');
      },
    });
  }

  closeDetail() {
    this.selectedConcern.set(null);
  }

  submitStatusUpdate() {
    const r = this.selectedConcern();
    if (!r) return;

    this.actionSubmitting.set(true);
    this.actionMessage.set(null);

    this.concernService
      .updateStaffConcernStatus(r.report_id, {
        status: this.newStatus(),
        public_notes: this.publicNotes().trim() || undefined,
        internal_notes: this.internalNotes().trim() || undefined,
        rejection_reason: this.rejectionReason().trim() || undefined,
        resolution_notes: this.resolutionNotes().trim() || undefined,
        citizen_reply_requested: this.citizenReplyRequested(),
      })
      .subscribe({
        next: (res) => {
          this.actionSubmitting.set(false);
          this.actionMessage.set(res.message);
          // Refresh detail and list
          this.openConcernDetail(r.report_id);
          this.loadConcerns();
        },
        error: (err) => {
          this.actionSubmitting.set(false);
          this.errorMessage.set(err.error?.error?.message || 'Failed to update concern status.');
        },
      });
  }

  assignSelectedHandler() {
    const r = this.selectedConcern();
    if (!r || !this.selectedHandlerId()) return;

    const handler = this.handlersList().find((h) => h.user_id === this.selectedHandlerId());
    if (!handler) return;

    this.actionSubmitting.set(true);
    this.concernService
      .assignHandler(r.report_id, handler.user_id, handler.display_name)
      .subscribe({
        next: (res) => {
          this.actionSubmitting.set(false);
          this.actionMessage.set(res.message);
          this.openConcernDetail(r.report_id);
          this.loadConcerns();
        },
        error: (err) => {
          this.actionSubmitting.set(false);
          this.errorMessage.set('Failed to assign handler.');
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
