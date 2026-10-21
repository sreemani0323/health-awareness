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
  readonly selectedOptionIds = signal<string[]>([]);
  readonly arrangedStepIds = signal<string[]>([]);
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

  readonly hasAnswerSelected = computed(() => {
    const card = this.currentCard();
    if (!card?.interaction) return false;
    const type = card.interaction.interaction_type;
    if (type === 'multi_select' || type === 'identify_risk') {
      return this.selectedOptionIds().length > 0;
    }
    if (type === 'arrange_steps') {
      return this.arrangedStepIds().length > 0;
    }
    return this.selectedOptionId() !== null;
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

  readonly missedQuestionsCount = computed(() => {
    const l = this.lesson();
    return l ? this.progressService.getMissedQuestions(l.id).length : 0;
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

        this.initCurrentCardState();
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

  toggleOptionSelection(optionId: string): void {
    if (this.answerSubmitted()) return;
    this.selectedOptionIds.update((current) =>
      current.includes(optionId)
        ? current.filter((id) => id !== optionId)
        : [...current, optionId],
    );
  }

  moveStep(index: number, direction: 'up' | 'down'): void {
    if (this.answerSubmitted()) return;
    const current = [...this.arrangedStepIds()];
    const targetIdx = direction === 'up' ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= current.length) return;
    const temp = current[index];
    current[index] = current[targetIdx];
    current[targetIdx] = temp;
    this.arrangedStepIds.set(current);
  }

  submitAnswer(): void {
    const card = this.currentCard();
    if (!card?.interaction) return;

    const interactionType = card.interaction.interaction_type;
    const l = this.lesson();

    if (interactionType === 'multi_select' || interactionType === 'identify_risk') {
      const selected = this.selectedOptionIds();
      const correctIds = card.interaction.options
        .filter((o) => o.is_correct)
        .map((o) => o.id);

      const isCorrect =
        selected.length === correctIds.length &&
        selected.every((id) => correctIds.includes(id));

      this.answerSubmitted.set(true);
      this.answerCorrect.set(isCorrect);

      if (isCorrect) {
        const correctFeedback = card.interaction.options
          .filter((o) => o.is_correct)
          .map((o) => o.feedback)
          .join(' ');
        this.feedbackText.set(correctFeedback || 'Excellent! All selections are accurate.');
      } else {
        const wrongSelected = selected.filter((id) => !correctIds.includes(id));
        const missed = correctIds.filter((id) => !selected.includes(id));

        if (wrongSelected.length > 0) {
          const wrongOpt = card.interaction.options.find(
            (o) => o.id === wrongSelected[0],
          );
          this.feedbackText.set(
            wrongOpt?.feedback || 'One or more selected items are not risks or factors in this scenario.',
          );
        } else if (missed.length > 0) {
          const missedOpt = card.interaction.options.find(
            (o) => o.id === missed[0],
          );
          this.feedbackText.set(
            `Good start! Make sure to also check: ${missedOpt?.label}.`,
          );
        } else {
          this.feedbackText.set('Review your choices and try again.');
        }

        if (l) {
          this.progressService.recordMissedQuestion(
            l.id,
            card.interaction.question_prompt,
          );
        }
      }
    } else if (interactionType === 'arrange_steps') {
      const currentOrder = this.arrangedStepIds();
      const expected =
        card.interaction.correct_order ||
        card.interaction.options.map((o) => o.id);

      const isCorrect =
        JSON.stringify(currentOrder) === JSON.stringify(expected);

      this.answerSubmitted.set(true);
      this.answerCorrect.set(isCorrect);

      if (isCorrect) {
        this.feedbackText.set(
          card.interaction.options[0]?.feedback ||
            'Superb! You correctly arranged all steps in the verified public health sequence.',
        );
      } else {
        this.feedbackText.set(
          'The order is not quite right yet. Re-read the steps carefully and adjust the sequence.',
        );
        if (l) {
          this.progressService.recordMissedQuestion(
            l.id,
            card.interaction.question_prompt,
          );
        }
      }
    } else {
      // single_choice or myth_fact
      const selectedId = this.selectedOptionId();
      if (!selectedId) return;

      const selected = card.interaction.options.find(
        (o) => o.id === selectedId,
      );
      if (!selected) return;

      this.answerSubmitted.set(true);
      this.answerCorrect.set(selected.is_correct);
      this.feedbackText.set(selected.feedback);

      if (!selected.is_correct && l) {
        this.progressService.recordMissedQuestion(
          l.id,
          card.interaction.question_prompt,
        );
      }
    }
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
        this.shareToastMessage.set(
          'Lesson link copied to clipboard! Share it with family members.',
        );
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
    const card = this.currentCard();
    const isMulti =
      card?.interaction?.interaction_type === 'multi_select' ||
      card?.interaction?.interaction_type === 'identify_risk';

    const selected = isMulti
      ? this.selectedOptionIds().includes(option.id)
      : this.selectedOptionId() === option.id;

    const submitted = this.answerSubmitted();

    if (!submitted) {
      return selected ? `${base} ${base}--selected` : base;
    }

    if (option.is_correct) return `${base} ${base}--correct`;
    if (selected && !option.is_correct) return `${base} ${base}--incorrect`;
    return `${base} ${base}--disabled`;
  }

  getArrangedStep(stepId: string): AnswerOption | undefined {
    const card = this.currentCard();
    return card?.interaction?.options.find((o) => o.id === stepId);
  }

  getCardTypeLabel(type: string): string {
    switch (type) {
      case 'explanation':
        return '📖 Story & Concept';
      case 'interaction':
        return '🧠 Interactive Practice';
      case 'recap':
        return '🔄 Real-World Action';
      default:
        return type;
    }
  }

  private initCurrentCardState(): void {
    const card = this.currentCard();
    if (card?.interaction?.interaction_type === 'arrange_steps') {
      const opts = card.interaction.options.map((o) => o.id);
      // Reverse or rotate so learner starts with a scrambled sequence to arrange
      this.arrangedStepIds.set([...opts].reverse());
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
    this.selectedOptionIds.set([]);
    this.answerSubmitted.set(false);
    this.answerCorrect.set(false);
    this.feedbackText.set('');
    this.showSources.set(false);
    this.initCurrentCardState();
  }
}
