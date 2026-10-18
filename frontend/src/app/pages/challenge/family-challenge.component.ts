import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AnswerOption, LessonDetail } from '../../models/api.models';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface ChallengeQuestion {
  id: string;
  topicId: string;
  topicTitle: string;
  lessonId: string;
  lessonTitle: string;
  prompt: string;
  options: AnswerOption[];
  retryAllowed: boolean;
}

@Component({
  selector: 'ha-family-challenge',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './family-challenge.component.html',
  styleUrl: './family-challenge.component.css',
})
export class FamilyChallengeComponent implements OnInit {
  private readonly api = inject(ApiService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly questions = signal<ChallengeQuestion[]>([]);
  readonly currentIndex = signal(0);

  // Interaction state
  readonly selectedOptionId = signal<string | null>(null);
  readonly answerSubmitted = signal(false);
  readonly answerCorrect = signal(false);
  readonly feedbackText = signal('');

  // Challenge completion tracking
  readonly isCompleted = signal(false);
  readonly completedQuestions = signal<string[]>([]);

  // Computed signals
  readonly totalQuestions = computed(() => this.questions().length);
  readonly currentQuestion = computed(() => {
    const list = this.questions();
    return list[this.currentIndex()] ?? null;
  });

  readonly progressPercent = computed(() => {
    const total = this.totalQuestions();
    if (total === 0) return 0;
    return Math.round(((this.currentIndex() + 1) / total) * 100);
  });

  readonly isLastQuestion = computed(
    () => this.currentIndex() === this.totalQuestions() - 1,
  );

  ngOnInit(): void {
    this.loadChallengeFromPublishedLessons();
  }

  loadChallengeFromPublishedLessons(): void {
    this.loading.set(true);
    this.error.set(null);

    // Fetch published topics and lessons
    this.api.getTopics().subscribe({
      next: (topics) => {
        const coreTopicIds = ['topic-hygiene', 'topic-water', 'topic-mosquito', 'topic-vaccine'];
        const matchedTopics = topics.filter((t) => coreTopicIds.includes(t.id));

        if (matchedTopics.length === 0) {
          this.error.set('No published health topics available for the Family Challenge.');
          this.loading.set(false);
          return;
        }

        // Fetch lesson list for each topic
        const lessonQueries = matchedTopics.map((t) =>
          this.api.getTopicLessons(t.id).pipe(
            catchError(() => of([])),
          ),
        );

        forkJoin(lessonQueries).subscribe({
          next: (lessonGroups) => {
            // Collect the first published lesson ID from each topic
            const firstLessonIds: Array<{ topicId: string; topicTitle: string; lessonId: string }> = [];
            lessonGroups.forEach((lessons, idx) => {
              if (lessons.length > 0) {
                firstLessonIds.push({
                  topicId: matchedTopics[idx].id,
                  topicTitle: matchedTopics[idx].title,
                  lessonId: lessons[0].id,
                });
              }
            });

            if (firstLessonIds.length === 0) {
              this.error.set('No published lessons found to generate challenge questions.');
              this.loading.set(false);
              return;
            }

            // Fetch detail for each lesson to extract genuine knowledge checks
            const detailQueries = firstLessonIds.map((item) =>
              this.api.getLessonDetail(item.lessonId).pipe(
                catchError(() => of(null as LessonDetail | null)),
              ),
            );

            forkJoin(detailQueries).subscribe({
              next: (details) => {
                const challengeList: ChallengeQuestion[] = [];

                details.forEach((detail, idx) => {
                  if (!detail) return;
                  const item = firstLessonIds[idx];

                  // Find cards with interaction
                  const quizCards = detail.cards.filter(
                    (c) => c.card_type === 'interaction' && c.interaction,
                  );

                  if (quizCards.length > 0) {
                    const card = quizCards[0];
                    if (card.interaction) {
                      challengeList.push({
                        id: card.id,
                        topicId: item.topicId,
                        topicTitle: item.topicTitle,
                        lessonId: detail.id,
                        lessonTitle: detail.title,
                        prompt: card.interaction.question_prompt,
                        options: card.interaction.options,
                        retryAllowed: card.interaction.incorrect_behaviour === 'retry',
                      });
                    }
                  }
                });

                if (challengeList.length === 0) {
                  this.error.set('No published knowledge-check questions available.');
                } else {
                  this.questions.set(challengeList);
                }
                this.loading.set(false);
              },
              error: () => {
                this.error.set('Failed to load published lesson content.');
                this.loading.set(false);
              },
            });
          },
          error: () => {
            this.error.set('Unable to retrieve topic lessons.');
            this.loading.set(false);
          },
        });
      },
      error: () => {
        this.error.set('Unable to connect to published topics.');
        this.loading.set(false);
      },
    });
  }

  selectOption(optionId: string): void {
    if (this.answerSubmitted()) return;
    this.selectedOptionId.set(optionId);
  }

  submitAnswer(): void {
    const q = this.currentQuestion();
    if (!q || !this.selectedOptionId()) return;

    const opt = q.options.find((o) => o.id === this.selectedOptionId());
    if (!opt) return;

    this.answerSubmitted.set(true);
    this.answerCorrect.set(opt.is_correct);
    this.feedbackText.set(opt.feedback);

    if (opt.is_correct && !this.completedQuestions().includes(q.id)) {
      this.completedQuestions.update((list) => [...list, q.id]);
    }
  }

  retryQuestion(): void {
    this.selectedOptionId.set(null);
    this.answerSubmitted.set(false);
    this.answerCorrect.set(false);
    this.feedbackText.set('');
  }

  nextQuestion(): void {
    if (this.isLastQuestion()) {
      this.isCompleted.set(true);
      return;
    }

    this.currentIndex.update((i) => i + 1);
    this.resetInteraction();
  }

  restartChallenge(): void {
    this.currentIndex.set(0);
    this.isCompleted.set(false);
    this.resetInteraction();
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

  private resetInteraction(): void {
    this.selectedOptionId.set(null);
    this.answerSubmitted.set(false);
    this.answerCorrect.set(false);
    this.feedbackText.set('');
  }
}
