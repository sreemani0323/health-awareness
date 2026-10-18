import { Component, signal, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ComingSoonService } from '../../services/coming-soon.service';
import { LearningProgressService, PracticalActivity } from '../../services/learning-progress.service';

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

  readonly newsletterEmail = signal<string>('');
  readonly progressClearedNotice = signal<string | null>(null);

  get comingSoonMessage() {
    return this.comingSoonService.message;
  }

  get resumeState() {
    return this.progressService.resumeState();
  }

  get hasResume() {
    return this.progressService.hasResume();
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

  clearProgress(): void {
    this.progressService.clearAllProgress();
    this.progressClearedNotice.set('Learning progress on this device has been cleared.');
    setTimeout(() => {
      this.progressClearedNotice.set(null);
    }, 4000);
  }

  showComingSoon(featureName: string): void {
    this.comingSoonService.show(featureName);
  }

  onSubscribeNewsletter(): void {
    const email = this.newsletterEmail().trim();
    if (!email) {
      this.comingSoonService.show('Newsletter subscription');
      return;
    }
    this.comingSoonService.show('Newsletter subscription');
    this.newsletterEmail.set('');
  }
}
