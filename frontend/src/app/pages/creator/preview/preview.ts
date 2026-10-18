import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule, UpperCasePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import { CreatorVersion, CreatorCard } from '../../../models/creator.models';

@Component({
  selector: 'ha-draft-preview',
  standalone: true,
  imports: [CommonModule, RouterLink, UpperCasePipe],
  templateUrl: './preview.html',
  styleUrl: './preview.css',
})
export class PreviewComponent implements OnInit {
  readonly version = signal<CreatorVersion | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly actionMessage = signal<string | null>(null);

  /** Index of currently displayed card (0-based) */
  readonly currentCardIndex = signal(0);

  /** Quiz interaction state for current card */
  readonly selectedOptionId = signal<string | null>(null);
  readonly answerSubmitted = signal(false);
  readonly answerCorrect = signal(false);
  readonly feedbackText = signal('');
  readonly showSources = signal(false);

  /** Computed signals */
  readonly totalCards = computed(() => this.version()?.cards.length ?? 0);
  readonly currentCard = computed(() => {
    const v = this.version();
    if (!v || v.cards.length === 0) return null;
    return v.cards[this.currentCardIndex()] ?? null;
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

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    public readonly creatorApi: CreatorApiService,
  ) {}

  ngOnInit(): void {
    const versionId = this.route.snapshot.paramMap.get('versionId') ?? '';
    if (!versionId) {
      this.error.set('No version ID specified.');
      this.loading.set(false);
      return;
    }

    this.creatorApi.getVersion(versionId).subscribe({
      next: (v) => {
        this.version.set(v);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(
          err?.error?.error?.message ||
            'Failed to load draft version. Authentication required.',
        );
        this.loading.set(false);
      },
    });
  }

  getCardTypeLabel(type: string): string {
    switch (type) {
      case 'explanation':
        return 'Health Concept';
      case 'interaction':
        return 'Knowledge Check';
      case 'recap':
        return 'Lesson Summary';
      default:
        return 'Lesson Card';
    }
  }

  selectOption(optionId: string): void {
    if (this.answerSubmitted()) return;
    this.selectedOptionId.set(optionId);
  }

  submitAnswer(): void {
    const card = this.currentCard();
    if (!card || !card.interaction || !this.selectedOptionId()) return;

    const opt = card.interaction.options.find(
      (o) => o.id === this.selectedOptionId(),
    );
    if (!opt) return;

    this.answerSubmitted.set(true);
    this.answerCorrect.set(opt.is_correct);
    this.feedbackText.set(
      opt.feedback ||
        (opt.is_correct
          ? 'Correct! Well done.'
          : 'Not quite. Review the explanation and try again.'),
    );
  }

  nextCard(): void {
    if (this.currentCardIndex() < this.totalCards() - 1) {
      this.currentCardIndex.update((i) => i + 1);
      this.resetInteractionState();
    }
  }

  prevCard(): void {
    if (this.currentCardIndex() > 0) {
      this.currentCardIndex.update((i) => i - 1);
      this.resetInteractionState();
    }
  }

  toggleSources(): void {
    this.showSources.update((v) => !v);
  }

  restart(): void {
    this.currentCardIndex.set(0);
    this.resetInteractionState();
  }

  submitForReview(): void {
    const v = this.version();
    if (!v) return;

    this.creatorApi.submitForReview(v.id).subscribe({
      next: (updated) => {
        this.version.set(updated);
        this.actionMessage.set('Draft successfully submitted for review!');
      },
      error: (err) => {
        this.actionMessage.set(
          'Submission failed: ' + (err?.error?.error?.message || err.message),
        );
      },
    });
  }

  approveAndPublish(): void {
    const v = this.version();
    if (!v) return;

    if (!confirm(`Publish version "${v.title}" to all learners?`)) return;

    this.creatorApi.approveVersion(v.id).subscribe({
      next: (updated) => {
        this.version.set(updated);
        this.actionMessage.set('Version approved and published successfully!');
      },
      error: (err) => {
        this.actionMessage.set(
          'Approval failed: ' + (err?.error?.error?.message || err.message),
        );
      },
    });
  }

  private resetInteractionState(): void {
    this.selectedOptionId.set(null);
    this.answerSubmitted.set(false);
    this.answerCorrect.set(false);
    this.feedbackText.set('');
  }
}
