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

export type ApplicationStep = 'details' | 'email_otp' | 'sms_otp_and_password' | 'success';

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

  // Step 2 & 3: Verification & Password Fields
  emailOtp = signal<string>('');
  smsOtp = signal<string>('');
  maskedPhone = signal<string>('');
  newPassword = signal<string>('');
  confirmPassword = signal<string>('');
  showPassword = signal<boolean>(false);

  // Step 4: Submission Result
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
    if (this.cooldownInterval) {
      clearInterval(this.cooldownInterval);
    }
  }

  selectRole(roleId: string): void {
    this.requestedRole.set(roleId);
  }

  toggleShowPassword(): void {
    this.showPassword.set(!this.showPassword());
  }

  private startCooldown(seconds: number = 60): void {
    this.resendCooldown.set(seconds);
    if (this.cooldownInterval) clearInterval(this.cooldownInterval);
    this.cooldownInterval = setInterval(() => {
      const current = this.resendCooldown();
      if (current <= 1) {
        this.resendCooldown.set(0);
        clearInterval(this.cooldownInterval);
      } else {
        this.resendCooldown.set(current - 1);
      }
    }, 1000);
  }

  // --- Step 1: Submit Details & Request Email OTP ---
  submitApplication(): void {
    this.errorMessage.set(null);
    this.infoMessage.set(null);

    const name = this.applicantName().trim();
    const email = this.applicantEmail().trim();
    const phone = this.applicantPhone().trim();
    const sop = this.statementOfPurpose().trim();

    if (!name) {
      this.errorMessage.set('Please provide your full legal or professional name.');
      return;
    }
    if (!email || !email.includes('@')) {
      this.errorMessage.set('Please provide a valid contact email address.');
      return;
    }
    if (!phone || phone.length < 10) {
      this.errorMessage.set('Please provide a valid mobile number in international or national format (e.g. +91 98765 43210).');
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

    const payload = {
      applicant_name: name,
      applicant_email: email,
      applicant_phone: phone,
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

    this.creatorApi.initiateRoleRequest(payload).subscribe({
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

  // --- Step 2: Verify Email OTP ---
  verifyEmailOtp(): void {
    this.errorMessage.set(null);
    this.infoMessage.set(null);

    const email = this.applicantEmail().trim();
    const otp = this.emailOtp().trim();

    if (!otp || otp.length < 6) {
      this.errorMessage.set('Please enter the 6-digit verification code received in your email.');
      return;
    }

    this.submitting.set(true);

    this.creatorApi.verifyRoleRequestEmail(email, otp).subscribe({
      next: (res) => {
        this.maskedPhone.set(res.masked_phone || this.applicantPhone());
        // Automatically dispatch SMS OTP
        this.creatorApi.sendRoleRequestSms(email, this.applicantPhone().trim()).subscribe({
          next: (smsRes) => {
            this.submitting.set(false);
            this.infoMessage.set(smsRes.message || 'Email verified! An SMS OTP has been sent to your mobile phone.');
            this.currentStep.set('sms_otp_and_password');
            this.startCooldown(60);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          },
          error: () => {
            // Even if SMS auto-send had an error, transition to step 3 so user can resend
            this.submitting.set(false);
            this.infoMessage.set('Email verified! Please request an SMS code to verify your phone.');
            this.currentStep.set('sms_otp_and_password');
            window.scrollTo({ top: 0, behavior: 'smooth' });
          },
        });
      },
      error: (err) => {
        this.submitting.set(false);
        const errObj = err.error?.error || err.error || {};
        this.errorMessage.set(errObj.message || 'Invalid or expired email verification code.');
      },
    });
  }

  resendEmailOtp(): void {
    if (this.resendCooldown() > 0) return;
    this.submitApplication();
  }

  resendSmsOtp(): void {
    if (this.resendCooldown() > 0) return;
    this.errorMessage.set(null);
    this.infoMessage.set(null);

    this.creatorApi.sendRoleRequestSms(this.applicantEmail().trim(), this.applicantPhone().trim()).subscribe({
      next: (res) => {
        this.infoMessage.set(res.message || 'New SMS verification code dispatched.');
        this.startCooldown(60);
      },
      error: (err) => {
        const errObj = err.error?.error || err.error || {};
        this.errorMessage.set(errObj.message || 'Failed to resend SMS code. Please try again.');
      },
    });
  }

  // --- Step 3: Complete Registration (Verify SMS OTP & Set Password) ---
  completeRegistration(): void {
    this.errorMessage.set(null);
    this.infoMessage.set(null);

    const email = this.applicantEmail().trim();
    const phone = this.applicantPhone().trim();
    const smsOtp = this.smsOtp().trim();
    const pwd = this.newPassword();
    const confirm = this.confirmPassword();

    if (!smsOtp || smsOtp.length < 6) {
      this.errorMessage.set('Please enter the 6-digit SMS OTP received on your mobile phone.');
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
      phone,
      sms_otp: smsOtp,
      password: pwd,
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
        this.errorMessage.set(errObj.message || 'Failed to complete registration. Please check your SMS code and try again.');
      },
    });
  }

  backToDetails(): void {
    this.currentStep.set('details');
    this.errorMessage.set(null);
    this.infoMessage.set(null);
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
