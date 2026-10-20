import { Component, signal, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ComingSoonService } from '../../services/coming-soon.service';
import { LearnerAuthService } from '../../services/learner-auth.service';

@Component({
  selector: 'ha-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css',
})
export class NavbarComponent {
  private readonly comingSoonService = inject(ComingSoonService);
  readonly learnerAuth = inject(LearnerAuthService, { optional: true });

  readonly isMobileMenuOpen = signal<boolean>(false);

  toggleMobileMenu(): void {
    this.isMobileMenuOpen.update((v) => !v);
  }

  closeMobileMenu(): void {
    this.isMobileMenuOpen.set(false);
  }

  onComingSoonClick(featureName: string, event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.closeMobileMenu();
    this.comingSoonService.show(featureName);
  }

  onSaveProgressClick(): void {
    this.closeMobileMenu();
    this.comingSoonService.show(
      'Cloud sync (Neon Auth): Learning progress is automatically saved on this device. Cloud account sync is coming in Stage 2!'
    );
  }

  onSignOutClick(): void {
    this.closeMobileMenu();
    this.learnerAuth?.logout();
  }
}
