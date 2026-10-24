import { Component, inject, computed } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LearningProgressService } from '../../services/learning-progress.service';

@Component({
  selector: 'ha-bottom-nav',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './bottom-nav.component.html',
  styleUrl: './bottom-nav.component.css',
})
export class BottomNavComponent {
  private readonly progressService = inject(LearningProgressService, { optional: true });

  readonly completedLessonsCount = computed<number>(() => {
    return this.progressService?.completedCount() ?? 0;
  });
}
