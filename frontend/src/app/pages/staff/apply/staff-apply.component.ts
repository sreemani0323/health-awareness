import { Component, inject, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';

interface RoleOption {
  id: string;
  title: string;
  badge: string;
  description: string;
  icon: string;
}

export type ApplicationStep = 'details' | 'email_otp' | 'success';

@Component({
  selector: 'app-staff-apply',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './staff-apply.component.html',
  styleUrls: ['./staff-apply.component.css'],
})
export class StaffApplyComponent implements OnDestroy {
  private creatorApi = inject(CreatorApiService);
  private router = inject(Router);

  // Workflow Step Management
  currentStep = signal<ApplicationStep>('details');
  submitting = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  infoMessage = signal<string | null>(null);
  copied = signal<boolean>(false);

  // Cooldown timers
  resendCooldown = signal<number>(0);
  private cooldownInterval: any = null;

  // Step 1: Form Fields
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

  // Step 2: Verification & Password Fields
  emailOtp = signal<string>('');
  newPassword = signal<string>('');
  confirmPassword = signal<string>('');
  showPassword = signal<boolean>(false);

  // Step 3: Submission Result
  submissionResult = signal<{
    reference_id: string;
    tracking_token: string;
    status: string;
    message: string;
    requested_role?: string;
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

  ngOnDestroy(): void {
    this.stopCooldown();
  }

  selectRole(roleId: string): void {
    this.requestedRole.set(roleId);
  }

  toggleShowPassword(): void {
    this.showPassword.update((val) => !val);
  }

  private startCooldown(seconds: number): void {
    this.stopCooldown();
    this.resendCooldown.set(seconds);
    this.cooldownInterval = setInterval(() => {
      const cur = this.resendCooldown();
      if (cur <= 1) {
        this.stopCooldown();
      } else {
        this.resendCooldown.set(cur - 1);
      }
    }, 1000);
  }

  private stopCooldown(): void {
    if (this.cooldownInterval) {
      clearInterval(this.cooldownInterval);
      this.cooldownInterval = null;
    }
    this.resendCooldown.set(0);
  }

  // --- Step 1: Submit Application Details & Initiate Email Verification ---
  submitApplication(): void {
    this.errorMessage.set(null);
    this.infoMessage.set(null);

    const name = this.applicantName().trim();
    const email = this.applicantEmail().trim();
    const phone = this.applicantPhone().trim();
    const role = this.requestedRole();
    const sop = this.statementOfPurpose().trim();
    const evAck = this.evidenceStandardsAcknowledged();
    const csAck = this.childSafetyAcknowledged();

    if (!name) {
      this.errorMessage.set('Please enter your full legal name.');
      return;
    }
    if (!email || !email.includes('@')) {
      this.errorMessage.set('Please enter a valid email address.');
      return;
    }
    if (!role) {
      this.errorMessage.set('Please select the role you are applying for.');
      return;
    }
    if (sop.length < 30) {
      this.errorMessage.set('Statement of purpose must be at least 30 characters long.');
      return;
    }
    if (!evAck) {
      this.errorMessage.set('You must acknowledge evidence-based health standards.');
      return;
    }
    if (!csAck) {
      this.errorMessage.set('You must acknowledge learner safety guidelines.');
      return;
    }

    this.submitting.set(true);

    this.creatorApi.initiateRoleRequest({
      name,
      applicant_name: name,
      email,
      applicant_email: email,
      phone: phone || undefined,
      applicant_phone: phone || undefined,
      role,
      requested_role: role,
      organization: this.organization().trim() || undefined,
      professional_title: this.professionalTitle().trim() || undefined,
      credential_reference: this.credentialReference().trim() || undefined,
      portfolio_url: this.portfolioUrl().trim() || undefined,
      statement_of_purpose: sop,
      evidence_standards_acknowledged: evAck,
      child_safety_acknowledged: csAck,
    }).subscribe({
      next: (res) => {
        this.submitting.set(false);
        this.infoMessage.set(res.message || `Verification code sent to ${email}. Please enter the 6-digit code.`);
        this.currentStep.set('email_otp');
        this.startCooldown(60);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: (err) => {
        this.submitting.set(false);
        const errObj = err.error?.error || err.error || {};
        const msg = errObj.message || 'Failed to initiate application. Please check your inputs and try again.';
        this.errorMessage.set(msg);
      },
    });
  }

  // --- Step 2: Complete Registration (Verify Email OTP & Set Password) ---
  completeRegistration(): void {
    this.errorMessage.set(null);
    this.infoMessage.set(null);

    const email = this.applicantEmail().trim();
    const phone = this.applicantPhone().trim();
    const emailOtp = this.emailOtp().trim();
    const pwd = this.newPassword();
    const confirm = this.confirmPassword();

    if (!emailOtp || emailOtp.length < 6) {
      this.errorMessage.set('Please enter the 6-digit verification code sent to your email.');
      return;
    }
    if (!pwd || pwd.length < 8) {
      this.errorMessage.set('Password must be at least 8 characters long.');
      return;
    }
    if (pwd !== confirm) {
      this.errorMessage.set('Passwords do not match. Please re-enter your password.');
      return;
    }
    if (!/[A-Z]/.test(pwd) || !/[a-z]/.test(pwd) || !/[0-9\W]/.test(pwd)) {
      this.errorMessage.set('Password must include uppercase, lowercase, and a number or symbol.');
      return;
    }

    this.submitting.set(true);

    this.creatorApi.completeRoleRequest({
      email,
      email_otp: emailOtp,
      password: pwd,
      phone: phone || undefined,
    }).subscribe({
      next: (res) => {
        this.submitting.set(false);
        this.submissionResult.set(res);
        this.currentStep.set('success');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: (err) => {
        this.submitting.set(false);
        const errObj = err.error?.error || err.error || {};
        this.errorMessage.set(errObj.message || 'Failed to complete registration. Please check your verification code and try again.');
      },
    });
  }

  resendEmailOtp(): void {
    if (this.resendCooldown() > 0) return;
    this.submitApplication();
  }

  backToDetails(): void {
    this.currentStep.set('details');
    this.errorMessage.set(null);
    this.infoMessage.set(null);
  }

  copyCredentials(): void {
    const res = this.submissionResult();
    if (!res) return;
    const textToCopy = `HealthAware Application Credentials\nReference ID: ${res.reference_id}\nTracking Token: ${res.tracking_token}\nRequested Role: ${res.requested_role}`;
    navigator.clipboard.writeText(textToCopy).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 3000);
    });
  }

  goToStatus(): void {
    const res = this.submissionResult();
    if (res?.reference_id) {
      this.router.navigate(['/staff/application-status'], {
        queryParams: { reference_id: res.reference_id },
      });
    } else {
      this.router.navigate(['/staff/application-status']);
    }
  }
}
