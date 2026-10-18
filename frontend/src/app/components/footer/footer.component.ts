import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ComingSoonService } from '../../services/coming-soon.service';

@Component({
  selector: 'ha-footer',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.css',
})
export class FooterComponent {
  private readonly comingSoonService = inject(ComingSoonService);

  readonly currentYear = new Date().getFullYear();

  get comingSoonMessage() {
    return this.comingSoonService.message;
  }

  onComingSoonClick(featureName: string): void {
    this.comingSoonService.show(featureName);
  }
}
