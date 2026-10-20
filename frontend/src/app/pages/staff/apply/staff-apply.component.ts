import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import { PublicStaffApplicationSubmitRequest } from '../../../models/creator.models';

interface RoleOption {
  id: string;
  title: string;
  badge: string;
  description: string;
  icon: string;
}

@Component({
  selector: 'app-staff-apply',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './staff-apply.component.html',
  styleUrls: ['./staff-apply.component.css'],
})
export class StaffApplyComponent {
  private creatorApi = inject(CreatorApiService);
  private router = inject(Router);

  // Submission State
  submitting = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  copied = signal<boolean>(false);

  // Form Fields
  applicantName = signal<string>('');
  applicantEmail = signal<string>('');
  applicantPhone = signal<string>('');
  requestedRole = signal<string>('contributor');
  organization = signal<string>('');
  professionalTitle = signal<string>('');
  credentialReference = signal<string>('');
  portfolioUrl = signal<string>('');
  statementOfPurpose = signal<string>('');
  evidenceStandardsAcknowledged = signal<boolean>(false);
  childSafetyAcknowledged = signal<boolean>(false);

  // Result
  submissionResult = signal<{
    reference_id: string;
    tracking_token: string;
    status: string;
    message: string;
  } | null>(null);

  roles: RoleOption[] = [
    {
      id: 'contributor',
      title: 'Curriculum Contributor',
      badge: 'Content & Translation',
      description: 'Draft evidence-based lesson cards, micro-interactions, and local language translations.',
      icon: '✍️',
    },
    {
      id: 'reviewer',
      title: 'Medical & Editorial Reviewer',
      badge: 'Vetting & Quality',
      description: 'Validate clinical accuracy, WHO/ICMR alignment, and educational clarity before publication.',
      icon: '🩺',
    },
    {
      id: 'case_handler',
      title: 'Case Triage Officer',
      badge: 'Community Escalation',
      description: 'Triage citizen health and sanitation reports, assign priorities, and communicate updates.',
      icon: '📋',
    },
    {
      id: 'jurisdiction_officer',
      title: 'Jurisdiction Sanitation Officer',
      badge: 'Municipal Coordination',
      description: 'Coordinate localized response with municipal health workers in assigned districts.',
      icon: '🏛️',
    },
  ];

  selectRole(roleId: string): void {
    this.requestedRole.set(roleId);
  }

  submitApplication(): void {
    this.errorMessage.set(null);

    // Frontend validations
    const name = this.applicantName().trim();
    const email = this.applicantEmail().trim();
    const sop = this.statementOfPurpose().trim();

    if (!name) {
      this.errorMessage.set('Please provide your full legal or professional name.');
      return;
    }
    if (!email || !email.includes('@')) {
      this.errorMessage.set('Please provide a valid contact email address.');
      return;
    }
    if (sop.length < 30) {
      this.errorMessage.set('Statement of purpose must be at least 30 characters explaining your background.');
      return;
    }
    if (!this.evidenceStandardsAcknowledged()) {
      this.errorMessage.set('You must acknowledge HealthAware’s evidence-based health standards.');
      return;
    }
    if (!this.childSafetyAcknowledged()) {
      this.errorMessage.set('You must acknowledge learner safety guidelines.');
      return;
    }

    const payload: PublicStaffApplicationSubmitRequest = {
      applicant_name: name,
      applicant_email: email,
      applicant_phone: this.applicantPhone().trim() || undefined,
      requested_role: this.requestedRole(),
      organization: this.organization().trim() || undefined,
      professional_title: this.professionalTitle().trim() || undefined,
      credential_reference: this.credentialReference().trim() || undefined,
      portfolio_url: this.portfolioUrl().trim() || undefined,
      statement_of_purpose: sop,
      evidence_standards_acknowledged: this.evidenceStandardsAcknowledged(),
      child_safety_acknowledged: this.childSafetyAcknowledged(),
    };

    this.submitting.set(true);

    this.creatorApi.submitStaffApplication(payload).subscribe({
      next: (res) => {
        this.submitting.set(false);
        this.submissionResult.set(res);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: (err) => {
        this.submitting.set(false);
        const errObj = err.error?.error || err.error || {};
        const msg = errObj.message || 'Failed to submit application. Please check your inputs and try again.';
        this.errorMessage.set(msg);
      },
    });
  }

  copyCredentials(): void {
    const res = this.submissionResult();
    if (!res) return;
    const text = `HealthAware Staff Application\nReference ID: ${res.reference_id}\nTracking Token: ${res.tracking_token}\nTrack at: ${window.location.origin}/staff/application-status`;
    navigator.clipboard.writeText(text).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 3000);
    });
  }

  goToStatus(): void {
    const res = this.submissionResult();
    if (res) {
      this.router.navigate(['/staff/application-status'], {
        queryParams: { ref: res.reference_id, token: res.tracking_token },
      });
    }
  }
}
