import { Component, OnInit, computed, signal, inject } from '@angular/core';
import { UpperCasePipe, CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { LessonDetail, LessonCard, AnswerOption } from '../../models/api.models';
import { LearningProgressService, PracticalActivity } from '../../services/learning-progress.service';

@Component({
  selector: 'ha-lesson-player',
  standalone: true,
  imports: [CommonModule, RouterLink, UpperCasePipe],
  templateUrl: './lesson-player.component.html',
  styleUrl: './lesson-player.component.css',
})
export class LessonPlayerComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  readonly progressService = inject(LearningProgressService);

  readonly lesson = signal<LessonDetail | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  /** Index of the currently displayed card (0-based). */
  readonly currentCardIndex = signal(0);

  /** Interaction state for the current card. */
  readonly selectedOptionId = signal<string | null>(null);
  readonly answerSubmitted = signal(false);
  readonly answerCorrect = signal(false);
  readonly feedbackText = signal('');
  readonly showSources = signal(false);

  /** Share toast notification. */
  readonly shareToastMessage = signal<string | null>(null);

  /** Derived signals. */
  readonly totalCards = computed(() => this.lesson()?.cards.length ?? 0);
  readonly currentCard = computed(() => {
    const l = this.lesson();
    if (!l) return null;
    return l.cards[this.currentCardIndex()] ?? null;
  });
  readonly progressPercent = computed(() => {
    const total = this.totalCards();
    if (total === 0) return 0;
    return Math.round(((this.currentCardIndex() + 1) / total) * 100);
  });
  readonly isFirstCard = computed(() => this.currentCardIndex() === 0);
  readonly isLastCard = computed(
    () => this.currentCardIndex() === this.totalCards() - 1,
  );
  readonly canProceed = computed(() => {
    const card = this.currentCard();
    if (!card) return false;
    if (card.card_type !== 'interaction') return true;
    return this.answerSubmitted();
  });

  /** Associated practical activity for takeaway. */
  readonly associatedActivity = computed<PracticalActivity | null>(() => {
    const l = this.lesson();
    if (!l) return null;
    const activities = this.progressService.getPracticalActivities();
    return (
      activities.find((a) => a.relatedLessonId === l.id) ||
      activities.find((a) => a.topicId === l.topic_id) ||
      null
    );
  });

  readonly isCompletedOnDevice = computed(() => {
    const l = this.lesson();
    return l ? this.progressService.isLessonCompleted(l.id) : false;
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('lessonId') ?? '';
    this.api.getLessonDetail(id).subscribe({
      next: (detail) => {
        this.lesson.set(detail);
        this.loading.set(false);

        const stepParam = this.route.snapshot.queryParamMap?.get('step');
        if (stepParam) {
          const stepIdx = parseInt(stepParam, 10) - 1;
          if (!isNaN(stepIdx) && stepIdx >= 0 && stepIdx < detail.cards.length) {
            this.currentCardIndex.set(stepIdx);
          }
        }

        const answerParam = this.route.snapshot.queryParamMap?.get('answer');
        if (answerParam) {
          this.selectOption(answerParam);
          this.submitAnswer();
        }

        const sourcesParam = this.route.snapshot.queryParamMap?.get('sources');
        if (sourcesParam === 'true' || sourcesParam === '1') {
          this.showSources.set(true);
        }

        // Save initial resume position
        this.saveCurrentProgress();
      },
      error: () => {
        this.error.set('Unable to load this lesson. Please try again.');
        this.loading.set(false);
      },
    });
  }

  nextCard(): void {
    if (this.isLastCard()) return;
    this.currentCardIndex.update((i) => i + 1);
    this.resetInteraction();
    this.saveCurrentProgress();
  }

  prevCard(): void {
    if (this.isFirstCard()) return;
    this.currentCardIndex.update((i) => i - 1);
    this.resetInteraction();
    this.saveCurrentProgress();
  }

  goToCard(index: number): void {
    this.currentCardIndex.set(index);
    this.resetInteraction();
    this.saveCurrentProgress();
  }

  selectOption(optionId: string): void {
    if (this.answerSubmitted()) return;
    this.selectedOptionId.set(optionId);
  }

  submitAnswer(): void {
    const card = this.currentCard();
    if (!card?.interaction || !this.selectedOptionId()) return;

    const selected = card.interaction.options.find(
      (o) => o.id === this.selectedOptionId(),
    );
    if (!selected) return;

    this.answerSubmitted.set(true);
    this.answerCorrect.set(selected.is_correct);
    this.feedbackText.set(selected.feedback);
  }

  retryQuestion(): void {
    this.resetInteraction();
  }

  toggleSources(): void {
    this.showSources.update((v) => !v);
  }

  onCompleteLesson(): void {
    const l = this.lesson();
    if (l) {
      this.progressService.markLessonCompleted(l.id, l.topic_id);
    }
  }

  toggleActivity(activityId: string): void {
    this.progressService.toggleActivity(activityId);
  }

  isActivityCompleted(activityId: string): boolean {
    return this.progressService.isActivityCompleted(activityId);
  }

  async shareLesson(): Promise<void> {
    const l = this.lesson();
    if (!l) return;

    const publicUrl = `${window.location.origin}/lessons/${l.id}`;
    const shareData = {
      title: `${l.title} — HealthAware`,
      text: `Learn about ${l.title} on HealthAware: evidence-based community health education.`,
      url: publicUrl,
    };

    if (navigator && 'share' in navigator) {
      try {
        await (navigator as Navigator).share(shareData);
        return;
      } catch (err: unknown) {
        if ((err as Error)?.name === 'AbortError') return;
      }
    }

    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(publicUrl);
        this.shareToastMessage.set('Lesson link copied to clipboard! Share it with family members.');
      } else {
        this.shareToastMessage.set(`Share link: ${publicUrl}`);
      }
    } catch {
      this.shareToastMessage.set(`Share link: ${publicUrl}`);
    }

    setTimeout(() => {
      this.shareToastMessage.set(null);
    }, 4000);
  }

  getOptionClass(option: AnswerOption): string {
    const base = 'quiz__option';
    const selected = this.selectedOptionId() === option.id;
    const submitted = this.answerSubmitted();

    if (!submitted) {
      return selected ? `${base} ${base}--selected` : base;
    }

    if (option.is_correct) return `${base} ${base}--correct`;
    if (selected && !option.is_correct) return `${base} ${base}--incorrect`;
    return `${base} ${base}--disabled`;
  }

  getCardTypeLabel(type: string): string {
    switch (type) {
      case 'explanation':
        return '📖 Explanation';
      case 'interaction':
        return '🧠 Quiz';
      case 'recap':
        return '🔄 Recap';
      default:
        return type;
    }
  }

  private saveCurrentProgress(): void {
    const l = this.lesson();
    if (l) {
      this.progressService.saveLessonProgress(
        l.id,
        l.title,
        l.topic_id,
        this.currentCardIndex(),
        this.totalCards(),
      );
    }
  }

  private resetInteraction(): void {
    this.selectedOptionId.set(null);
    this.answerSubmitted.set(false);
    this.answerCorrect.set(false);
    this.feedbackText.set('');
    this.showSources.set(false);
  }
}
