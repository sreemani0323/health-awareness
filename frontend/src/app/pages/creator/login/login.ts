import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  username = '';
  password = '';
  errorMessage = '';
  successMessage = '';
  isLoading = false;

  // Forgot password view state
  isRecoveryMode = false;
  recoveryStep: 'request' | 'verify' = 'request';
  recoveryIdentifier = '';
  recoveryOtp = '';
  newPassword = '';
  confirmPassword = '';

  constructor(
    private creatorApi: CreatorApiService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {
    if (this.creatorApi.isAuthenticated && this.creatorApi.currentUser) {
      this.routeToRoleLanding(this.creatorApi.currentUser.role);
    }
  }

  onSubmit(): void {
    if (!this.username.trim() || !this.password.trim()) {
      this.errorMessage = 'Please enter both username/email and password.';
      this.cdr.markForCheck();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.login({ username: this.username, password: this.password }).subscribe({
      next: (user) => {
        this.routeToRoleLanding(user.role);
      },
      error: (err: any) => {
        this.isLoading = false;
        this.errorMessage = err?.error?.error?.message || 'Login failed. Please check your credentials.';
        this.cdr.markForCheck();
      },
    });
  }

  toggleRecoveryMode(enable: boolean): void {
    this.isRecoveryMode = enable;
    this.recoveryStep = 'request';
    this.recoveryOtp = '';
    this.newPassword = '';
    this.confirmPassword = '';
    this.errorMessage = '';
    this.successMessage = '';
    if (enable && this.username.trim()) {
      this.recoveryIdentifier = this.username.trim();
    }
    this.cdr.markForCheck();
  }

  onSendRecoveryCode(): void {
    const id = this.recoveryIdentifier.trim();
    if (!id) {
      this.errorMessage = 'Please enter your username or registered email address.';
      this.cdr.markForCheck();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.recoverPassword(id).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.recoveryStep = 'verify';
        this.successMessage = res.message || 'If an account exists, a 6-digit verification code has been dispatched.';
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to dispatch recovery code.';
        this.cdr.markForCheck();
      },
    });
  }

  onResetPassword(): void {
    const id = this.recoveryIdentifier.trim();
    const otp = this.recoveryOtp.trim();
    const pw = this.newPassword.trim();

    if (!otp || otp.length !== 6) {
      this.errorMessage = 'Please enter the 6-digit verification code.';
      this.cdr.markForCheck();
      return;
    }
    if (pw.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters long with uppercase, lowercase, and numbers.';
      this.cdr.markForCheck();
      return;
    }
    if (pw !== this.confirmPassword.trim()) {
      this.errorMessage = 'Passwords do not match.';
      this.cdr.markForCheck();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.resetPassword(id, otp, pw).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.successMessage = res.message || 'Password updated successfully! You can now sign in.';
        this.username = id;
        this.password = '';
        setTimeout(() => {
          this.toggleRecoveryMode(false);
          this.cdr.markForCheck();
        }, 2000);
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to update password. Please check your verification code.';
        this.cdr.markForCheck();
      },
    });
  }

  private routeToRoleLanding(role: string): void {
    if (role === 'admin') {
      this.router.navigate(['/creator/admin']);
    } else if (role === 'reviewer') {
      this.router.navigate(['/creator/reviews']);
    } else {
      this.router.navigate(['/creator']);
    }
  }
}

