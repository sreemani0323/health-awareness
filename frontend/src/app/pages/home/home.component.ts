import { Component, signal, inject, computed, HostListener } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ComingSoonService } from '../../services/coming-soon.service';
import { LearningProgressService, PracticalActivity } from '../../services/learning-progress.service';
import { LearnerAuthService } from '../../services/learner-auth.service';
import { AppDistributionService } from '../../services/app-distribution.service';

@Component({
  selector: 'ha-home',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent {
  private readonly comingSoonService = inject(ComingSoonService);
  readonly progressService = inject(LearningProgressService);
  readonly learnerAuth = inject(LearnerAuthService, { optional: true });
  readonly distributionService = inject(AppDistributionService);

  openAndroidModal(): void {
    this.distributionService.openModal();
  }

  readonly newsletterEmail = signal<string>('');
  readonly newsletterSuccess = signal<string | null>(null);
  readonly newsletterError = signal<string | null>(null);
  readonly progressClearedNotice = signal<string | null>(null);

  // Clear confirmation dialog state
  readonly showClearConfirmation = signal<boolean>(false);
  readonly isClearingEntireDevice = signal<boolean>(false);

  @HostListener('document:keydown.escape')
  onEscapePress(): void {
    if (this.showClearConfirmation()) {
      this.closeClearConfirmation();
    }
  }

  get comingSoonMessage() {
    return this.comingSoonService.message;
  }

  get resumeState() {
    return this.progressService.resumeState();
  }

  get hasResume() {
    return this.progressService.hasResume();
  }

  /**
   * Determine if the resume lesson is actually marked completed in the progress model.
   */
  get isResumeCompleted(): boolean {
    const r = this.progressService.resumeState();
    if (!r) return false;
    return this.progressService.isLessonCompleted(r.lessonId) ||
      (r.cardIndex + 1 >= r.totalCards && this.progressService.isLessonCompleted(r.lessonId));
  }

  /**
   * Accurate percentage computation for active lesson progress bar.
   */
  get resumeProgressPercent(): number {
    const r = this.progressService.resumeState();
    if (!r || r.totalCards <= 0) return 0;
    return Math.min(100, Math.max(1, Math.round(((r.cardIndex + 1) / r.totalCards) * 100)));
  }

  get practicalActivities(): PracticalActivity[] {
    return this.progressService.getPracticalActivities();
  }

  get achievedMilestones() {
    return this.progressService.achievedMilestones();
  }

  get completedCount() {
    return this.progressService.completedCount();
  }

  get activitiesCount() {
    return this.progressService.activitiesCount();
  }

  isActivityCompleted(activityId: string): boolean {
    return this.progressService.isActivityCompleted(activityId);
  }

  toggleActivity(activityId: string): void {
    this.progressService.toggleActivity(activityId);
  }

  openClearBookmarkDialog(): void {
    this.isClearingEntireDevice.set(false);
    this.showClearConfirmation.set(true);
  }

  openClearAllDeviceDialog(): void {
    this.isClearingEntireDevice.set(true);
    this.showClearConfirmation.set(true);
  }

  closeClearConfirmation(): void {
    this.showClearConfirmation.set(false);
  }

  confirmClearProgress(): void {
    if (this.isClearingEntireDevice()) {
      this.progressService.clearAllProgress();
      this.progressClearedNotice.set('All local device learning records have been cleared.');
    } else {
      this.progressService.clearResumeProgress();
      this.progressClearedNotice.set('Saved lesson bookmark cleared. Your badges and completed lessons remain safe.');
    }
    this.closeClearConfirmation();
    setTimeout(() => {
      this.progressClearedNotice.set(null);
    }, 4000);
  }

  /** Backwards compatibility method for existing tests/callers */
  clearProgress(): void {
    this.confirmClearProgress();
  }

  showComingSoon(featureName: string): void {
    this.comingSoonService.show(featureName);
  }

  onSubscribeNewsletter(): void {
    const email = this.newsletterEmail().trim();
    if (!email || !email.includes('@') || !email.includes('.')) {
      this.newsletterSuccess.set(null);
      this.newsletterError.set('Please enter a valid email address (e.g., name@example.com).');
      setTimeout(() => {
        this.newsletterError.set(null);
      }, 5000);
      return;
    }
    this.newsletterError.set(null);
    this.newsletterSuccess.set(`Thank you for subscribing! Community health bulletins will be sent to ${email}.`);
    this.newsletterEmail.set('');
    setTimeout(() => {
      this.newsletterSuccess.set(null);
    }, 5000);
  }
}

