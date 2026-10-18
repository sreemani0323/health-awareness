import { Component, OnInit, signal, inject } from '@angular/core';
import { UpperCasePipe, CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { LessonSummary, Topic } from '../../models/api.models';
import { LearningProgressService, PracticalActivity } from '../../services/learning-progress.service';

@Component({
  selector: 'ha-topic-lessons',
  standalone: true,
  imports: [CommonModule, RouterLink, UpperCasePipe],
  templateUrl: './topic-lessons.component.html',
  styleUrl: './topic-lessons.component.css',
})
export class TopicLessonsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  readonly progressService = inject(LearningProgressService);

  readonly lessons = signal<LessonSummary[]>([]);
  readonly topicTitle = signal('');
  readonly topicDescription = signal('');
  readonly topicId = signal('');
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  isLessonCompleted(lessonId: string): boolean {
    return this.progressService.isLessonCompleted(lessonId);
  }

  getTopicActivity(): PracticalActivity | null {
    const activities = this.progressService.getPracticalActivities();
    return activities.find((a) => a.topicId === this.topicId()) || null;
  }

  toggleActivity(activityId: string): void {
    this.progressService.toggleActivity(activityId);
  }

  isActivityCompleted(activityId: string): boolean {
    return this.progressService.isActivityCompleted(activityId);
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('topicId') ?? '';
    this.topicId.set(id);

    // Fetch topic metadata for the header
    this.api.getTopics().subscribe({
      next: (topics) => {
        const topic = topics.find((t) => t.id === id);
        if (topic) {
          this.topicTitle.set(topic.title);
          this.topicDescription.set(topic.description);
        }
      },
    });

    // Fetch lessons for this topic
    this.api.getTopicLessons(id).subscribe({
      next: (lessons) => {
        this.lessons.set(lessons);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Unable to load lessons for this topic.');
        this.loading.set(false);
      },
    });
  }

  formatDuration(minutes: number): string {
    if (minutes < 60) return `${minutes} min`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }

  getTopicOutcomes(): string[] {
    const outcomes: Record<string, string[]> = {
      'topic-hygiene': [
        'Master the 5-step, 20-second handwashing technique with soap and running water',
        'Identify the 5 key everyday moments for hand hygiene in household, school, and community settings',
        'Understand how soap, friction, and rinsing mechanically lift and remove germs, dirt, and grease',
        'Learn proper hand drying with a clean towel or air drying to prevent immediate germ transfer',
      ],
      'topic-water': [
        'Understand why drinking water can become contaminated across collection, transport, treatment, and storage',
        'Explain the difference between microbial contamination and chemical contamination at a basic level',
        'Understand why water-treatment methods must match the relevant contamination risk and why official guidance matters',
        'Apply practical safe-water collection, storage, and handling principles to prevent recontamination',
        'Recognize how sanitation and hygiene practices help prevent drinking-water contamination',
      ],
      'topic-mosquito': [
        'Recognize standing water breeding habitats for Anopheles and Aedes mosquitoes',
        'Apply household barrier methods including insecticide-treated nets and source removal',
      ],
      'topic-vaccine': [
        'Understand the biological mechanism of vaccine-induced antibodies and immunity',
        'Identify key immunization milestones across childhood and family life stages',
      ],
    };
    return outcomes[this.topicId()] || [
      'Understand evidence-based public health practices for everyday prevention',
      'Apply verified guidance from WHO and public health authorities',
    ];
  }
}
