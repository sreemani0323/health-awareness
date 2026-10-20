import { Component, signal, inject, ViewChild } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ComingSoonService } from '../../services/coming-soon.service';
import { LearnerAuthService } from '../../services/learner-auth.service';
import { LearningProgressService } from '../../services/learning-progress.service';
import { LearnerAuthModalComponent } from '../learner-auth-modal/learner-auth-modal.component';

@Component({
  selector: 'ha-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, LearnerAuthModalComponent],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css',
})
export class NavbarComponent {
  private readonly comingSoonService = inject(ComingSoonService);
  readonly learnerAuth = inject(LearnerAuthService, { optional: true });
  readonly progressService = inject(LearningProgressService, { optional: true });

  @ViewChild(LearnerAuthModalComponent) authModal?: LearnerAuthModalComponent;

  readonly isMobileMenuOpen = signal<boolean>(false);

  toggleMobileMenu(): void {
    this.isMobileMenuOpen.update((v) => !v);
  }

  closeMobileMenu(): void {
    this.isMobileMenuOpen.set(false);
  }

  openLearnerAuth(tab: 'login' | 'register' = 'login'): void {
    this.closeMobileMenu();
    this.authModal?.open(tab);
  }

  onComingSoonClick(featureName: string, event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.closeMobileMenu();
    this.comingSoonService.show(featureName);
  }

  async onSyncClick(): Promise<void> {
    this.closeMobileMenu();
    if (this.progressService) {
      await this.progressService.syncWithRemote();
    }
  }

  onSaveProgressClick(): void {
    // Open learner auth modal to log in / create account and sync
    this.openLearnerAuth('login');
  }

  onSignOutClick(): void {
    this.closeMobileMenu();
    this.learnerAuth?.logout();
  }
}

