import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ComingSoonService } from '../../services/coming-soon.service';
import { AppDistributionService } from '../../services/app-distribution.service';
import { ApiConfigService } from '../../services/api-config.service';

@Component({
  selector: 'ha-footer',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.css',
})
export class FooterComponent {
  private readonly comingSoonService = inject(ComingSoonService);
  private readonly apiConfig = inject(ApiConfigService);
  readonly distribution = inject(AppDistributionService);

  readonly currentYear = new Date().getFullYear();

  get isNative(): boolean {
    return this.apiConfig.isNative;
  }

  get comingSoonMessage() {
    return this.comingSoonService.message;
  }

  onComingSoonClick(featureName: string): void {
    if (featureName.toLowerCase().includes('android')) {
      this.distribution.openModal();
      return;
    }
    this.comingSoonService.show(featureName);
  }
}
