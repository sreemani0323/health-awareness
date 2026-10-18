import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { Topic } from '../../models/api.models';

@Component({
  selector: 'ha-topics',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './topics.component.html',
  styleUrls: ['./topics.component.css'],
})
export class TopicsComponent implements OnInit {
  private readonly apiService = inject(ApiService);

  readonly topics = signal<Topic[]>([]);
  readonly loading = signal<boolean>(true);
  readonly error = signal<string | null>(null);
  readonly chapterCounts = signal<Record<string, number>>({});

  ngOnInit(): void {
    this.loadTopics();
  }

  loadTopics(): void {
    this.loading.set(true);
    this.error.set(null);

    this.apiService.getTopics().subscribe({
      next: (data) => {
        this.topics.set(data);
        this.loading.set(false);

        // Dynamically fetch lesson counts for each topic from API
        for (const topic of data) {
          if (typeof this.apiService.getTopicLessons === 'function') {
            this.apiService.getTopicLessons(topic.id).subscribe({
              next: (lessons) => {
                this.chapterCounts.update((counts) => ({
                  ...counts,
                  [topic.id]: lessons.length,
                }));
              },
              error: () => {
                // Silently fallback if lessons count cannot be retrieved
              },
            });
          }
        }
      },
      error: (err) => {
        this.error.set(
          err?.error?.error?.message ||
            'Unable to load health topics. Please check your connection and try again.'
        );
        this.loading.set(false);
      },
    });
  }

  getThumbnailColor(slug: string): string {
    const colors: Record<string, string> = {
      hygiene: '#00645c',
      water: '#0288d1',
      mosquito: '#f5701b',
      vaccine: '#6a1b9a',
    };
    return colors[slug] || '#00645c';
  }

  getDarkerThumbnailColor(slug: string): string {
    const colors: Record<string, string> = {
      hygiene: '#004d40',
      water: '#01579b',
      mosquito: '#d84315',
      vaccine: '#4a148c',
    };
    return colors[slug] || '#004d40';
  }

  getTopicIcon(slug: string): string {
    const icons: Record<string, string> = {
      hygiene: '🧼',
      water: '💧',
      mosquito: '🦟',
      vaccine: '💉',
    };
    return icons[slug] || '📚';
  }

  getTopicStatus(topicOrSlug: Topic | string): string {
    const topic = typeof topicOrSlug === 'string'
      ? this.topics().find((t) => t.slug === topicOrSlug || t.id === topicOrSlug)
      : topicOrSlug;

    const slug = topic ? topic.slug : (typeof topicOrSlug === 'string' ? topicOrSlug : '');
    const topicId = topic ? topic.id : (typeof topicOrSlug === 'string' ? topicOrSlug : '');

    const sourceMap: Record<string, string> = {
      hygiene: 'Verified WHO & CDC',
      water: 'Verified WHO & JJM',
      mosquito: 'Verified WHO & NVBDCP',
      vaccine: 'Verified WHO & MoHFW',
    };
    const authority = sourceMap[slug] || 'Verified Public Health Sources';

    const count = this.chapterCounts()[topicId];
    if (count !== undefined) {
      if (count === 0) {
        return `Coming Soon · ${authority}`;
      }
      const label = count === 1 ? '1 Complete Chapter' : `${count} Complete Chapters`;
      return `${label} · ${authority}`;
    }

    return `Curriculum · ${authority}`;
  }
}
