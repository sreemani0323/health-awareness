import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { UpperCasePipe, CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { LessonSummary, Topic, TopicMasteryChallenge } from '../../models/api.models';
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

  /** Topic Mastery Challenge state */
  readonly masteryChallenge = signal<TopicMasteryChallenge | null>(null);
  readonly showMasteryModal = signal(false);
  readonly masteryCurrentQuestionIdx = signal(0);
  readonly masterySelectedOptionId = signal<string | null>(null);
  readonly masteryAnswerSubmitted = signal(false);
  readonly masteryScore = signal(0);
  readonly masteryFinished = signal(false);

  readonly completedCount = computed(() =>
    this.lessons().filter((l) => this.isLessonCompleted(l.id)).length,
  );

  readonly progressPercentage = computed(() => {
    const total = this.lessons().length;
    return total > 0 ? Math.round((this.completedCount() / total) * 100) : 0;
  });

  readonly hasMasteryBadge = computed(() => {
    const id = this.topicId();
    const map: Record<string, string> = {
      'topic-hygiene': 'hygiene-topic-mastery',
      'topic-water': 'water-topic-mastery',
      'topic-mosquito': 'mosquito-topic-mastery',
      'topic-vaccine': 'vaccine-topic-mastery',
    };
    const badgeId = map[id];
    return this.progressService
      .achievedMilestones()
      .some((m) => m.id === badgeId);
  });

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

  openMasteryModal(): void {
    this.masteryCurrentQuestionIdx.set(0);
    this.masterySelectedOptionId.set(null);
    this.masteryAnswerSubmitted.set(false);
    this.masteryScore.set(0);
    this.masteryFinished.set(false);
    this.showMasteryModal.set(true);
  }

  closeMasteryModal(): void {
    this.showMasteryModal.set(false);
  }

  selectMasteryOption(id: string): void {
    if (this.masteryAnswerSubmitted()) return;
    this.masterySelectedOptionId.set(id);
  }

  submitMasteryAnswer(): void {
    const mc = this.masteryChallenge();
    if (!mc) return;
    const q = mc.questions[this.masteryCurrentQuestionIdx()];
    const opt = q.options.find((o) => o.id === this.masterySelectedOptionId());
    if (!opt) return;

    this.masteryAnswerSubmitted.set(true);
    if (opt.is_correct) {
      this.masteryScore.update((s) => s + 1);
    }
  }

  nextMasteryQuestion(): void {
    const mc = this.masteryChallenge();
    if (!mc) return;

    if (this.masteryCurrentQuestionIdx() < mc.questions.length - 1) {
      this.masteryCurrentQuestionIdx.update((i) => i + 1);
      this.masterySelectedOptionId.set(null);
      this.masteryAnswerSubmitted.set(false);
    } else {
      this.masteryFinished.set(true);
      this.progressService.recordTopicMastery(
        this.topicId(),
        this.masteryScore(),
        mc.questions.length,
      );
    }
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

    // Fetch topic mastery challenge
    if (typeof this.api.getTopicMastery === 'function') {
      this.api.getTopicMastery(id).subscribe({
        next: (challenge) => {
          this.masteryChallenge.set(challenge);
        },
        error: () => {
          // Non-fatal if mastery challenge not yet loaded
        },
      });
    }
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
