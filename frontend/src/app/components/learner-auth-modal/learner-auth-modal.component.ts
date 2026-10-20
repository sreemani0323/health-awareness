import { Component, signal, inject, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LearnerAuthService } from '../../services/learner-auth.service';
import { LearningProgressService } from '../../services/learning-progress.service';

@Component({
  selector: 'ha-learner-auth-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './learner-auth-modal.component.html',
  styleUrl: './learner-auth-modal.component.css',
})
export class LearnerAuthModalComponent {
  private readonly learnerAuth = inject(LearnerAuthService);
  private readonly progressService = inject(LearningProgressService, { optional: true });

  @Output() authSuccess = new EventEmitter<void>();

  readonly isOpen = signal<boolean>(false);
  readonly activeTab = signal<'login' | 'register' | 'recover'>('login');
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  // Form Fields
  displayName = '';
  email = '';
  password = '';
  confirmPassword = '';

  open(tab: 'login' | 'register' = 'login'): void {
    this.activeTab.set(tab);
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isOpen.set(true);
  }

  close(): void {
    this.isOpen.set(false);
    this.clearForm();
  }

  switchTab(tab: 'login' | 'register' | 'recover'): void {
    this.activeTab.set(tab);
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  private clearForm(): void {
    this.displayName = '';
    this.email = '';
    this.password = '';
    this.confirmPassword = '';
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  async onLogin(): Promise<void> {
    const trimmedEmail = this.email.trim();
    if (!trimmedEmail || !this.password) {
      this.errorMessage.set('Please provide both email and password.');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const result = await this.learnerAuth.login(trimmedEmail, this.password);
    this.isLoading.set(false);

    if (result.success) {
      this.successMessage.set('Signed in successfully!');
      if (this.progressService) {
        this.progressService.syncWithRemote().catch((e) => console.warn('Sync failed:', e));
      }
      this.authSuccess.emit();
      setTimeout(() => this.close(), 600);
    } else {
      this.errorMessage.set(result.error || 'Failed to sign in. Please verify your credentials.');
    }
  }

  async onRegister(): Promise<void> {
    const trimmedName = this.displayName.trim();
    const trimmedEmail = this.email.trim();

    if (!trimmedName) {
      this.errorMessage.set('Please enter your full name or nickname.');
      return;
    }
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      this.errorMessage.set('Please enter a valid email address.');
      return;
    }
    if (!this.password || this.password.length < 8) {
      this.errorMessage.set('Password must be at least 8 characters long.');
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.errorMessage.set('Passwords do not match.');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const result = await this.learnerAuth.register(trimmedName, trimmedEmail, this.password);
    this.isLoading.set(false);

    if (result.success) {
      this.successMessage.set('Account created and signed in!');
      if (this.progressService) {
        this.progressService.syncWithRemote().catch((e) => console.warn('Sync failed:', e));
      }
      this.authSuccess.emit();
      setTimeout(() => this.close(), 600);
    } else {
      this.errorMessage.set(result.error || 'Registration failed. Please try again.');
    }
  }

  async onRecover(): Promise<void> {
    const trimmedEmail = this.email.trim();
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      this.errorMessage.set('Please enter a valid email address.');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const result = await this.learnerAuth.recover(trimmedEmail);
    this.isLoading.set(false);

    if (result.success) {
      this.successMessage.set(
        result.message || 'If an account exists for this email, recovery instructions have been sent.'
      );
    } else {
      this.errorMessage.set(result.error || 'Unable to process recovery request.');
    }
  }
}
