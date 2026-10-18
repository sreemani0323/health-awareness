import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import {
  CreatorVersion,
  CreatorCard,
  CreatorContentBlock,
  CreatorInteraction,
  CreatorAnswerOption,
  CreatorLesson,
  CreatorTopic,
  CreatorSource,
} from '../../../models/creator.models';
import { CreatorNavbarComponent } from '../../../components/creator-navbar/creator-navbar.component';

export type SaveState = 'saved' | 'unsaved' | 'saving' | 'error';

@Component({
  selector: 'app-lesson-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CreatorNavbarComponent],
  templateUrl: './lesson-editor.html',
  styleUrl: './lesson-editor.css',
})
export class LessonEditor implements OnInit {
  lessonId = '';
  lesson: CreatorLesson | null = null;
  parentTopic: CreatorTopic | null = null;

  version: CreatorVersion | null = null;
  versions: CreatorVersion[] = [];

  // Active card selection in two-pane layout
  selectedCardIndex = 0;

  isLoading = true;
  saveState: SaveState = 'saved';
  saveMessage = '';
  errorMessage = '';

  // Validation warnings for current version & quiz
  validationErrors: string[] = [];

  // Medical Sources
  availableSources: CreatorSource[] = [];
  showAddSourceModal = false;
  newSourceTitle = '';
  newSourcePublisher = '';
  newSourceUrl = '';
  newSourceJurisdiction = '';
  isAddingSource = false;

  // Submit for review confirmation modal
  showSubmitModal = false;
  isSubmitting = false;

  constructor(
    public creatorApi: CreatorApiService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      this.lessonId = params.get('lessonId') || '';
      if (this.lessonId) {
        this.loadLessonAndCurriculum();
        this.loadSources();
      }
    });
  }

  loadLessonAndCurriculum(): void {
    this.isLoading = true;
    this.cdr.markForCheck();

    this.creatorApi.getLesson(this.lessonId).subscribe({
      next: (lesson) => {
        this.lesson = lesson;
        if (lesson.topic_id) {
          this.creatorApi.getTopic(lesson.topic_id).subscribe({
            next: (topic) => {
              this.parentTopic = topic;
              this.cdr.markForCheck();
            },
            error: () => {},
          });
        }
        this.loadVersions();
      },
      error: () => {
        // Fallback: load versions directly
        this.loadVersions();
      },
    });
  }

  loadVersions(): void {
    this.creatorApi.getVersions(this.lessonId).subscribe({
      next: (versions) => {
        this.versions = versions;
        // Prioritize active draft version, or submitted, or first version
        const draft = versions.find((v) => v.status === 'draft');
        const submitted = versions.find((v) => v.status === 'submitted_for_review');
        if (draft) {
          this.loadVersion(draft.id);
        } else if (submitted) {
          this.loadVersion(submitted.id);
        } else if (versions.length > 0) {
          this.loadVersion(versions[0].id);
        } else {
          // If no versions exist yet, auto-create initial draft version
          this.createInitialVersion();
        }
      },
      error: (err) => {
        this.isLoading = false;
        if (err?.status === 401) {
          this.router.navigate(['/creator/login']);
          return;
        }
        this.errorMessage = 'Failed to load chapter content versions.';
        this.cdr.markForCheck();
      },
    });
  }

  loadVersion(versionId: string): void {
    this.creatorApi.getVersion(versionId).subscribe({
      next: (version) => {
        this.version = version;
        this.selectedCardIndex = 0;
        this.saveState = 'saved';
        this.isLoading = false;
        this.runValidation();
        this.cdr.markForCheck();
      },
      error: () => {
        this.errorMessage = 'Failed to load chapter content version.';
        this.isLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  createInitialVersion(): void {
    const initialTitle = this.lesson?.title || this.lessonId.replace('lesson-', '').replace(/-/g, ' ');
    const newVerPayload: Partial<CreatorVersion> = {
      id: `ver-${this.lessonId}-v1`,
      title: initialTitle,
      summary: `Educational curriculum for ${initialTitle}`,
      learning_objectives: ['Understand core concepts'],
      cards: [
        {
          id: `card-${this.lessonId}-1`,
          position: 0,
          card_type: 'explanation',
          content_blocks: [
            { block_type: 'heading', body: initialTitle },
            { block_type: 'text', body: 'Introduce the core health concept for this chapter here.' },
          ],
          source_ids: [],
          interaction: null,
        },
      ],
    };

    this.creatorApi.createVersion(this.lessonId, newVerPayload).subscribe({
      next: (created) => {
        this.versions.push(created);
        this.version = created;
        this.selectedCardIndex = 0;
        this.saveState = 'saved';
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.isLoading = false;
        this.errorMessage = 'Failed to initialize chapter version.';
        this.cdr.markForCheck();
      },
    });
  }

  createRevision(): void {
    if (!this.version) return;
    this.isLoading = true;
    const nextVerNum = (this.version.version_number || 1) + 1;
    const newVerId = `ver-${this.lessonId}-v${nextVerNum}-${Date.now().toString().slice(-4)}`;

    const newVerPayload: Partial<CreatorVersion> = {
      id: newVerId,
      version_number: nextVerNum,
      title: this.version.title,
      summary: this.version.summary,
      language: this.version.language || 'en',
      learning_objectives: this.version.learning_objectives || ['Understand core concepts'],
      estimated_duration_minutes: this.version.estimated_duration_minutes || 5,
      cards: JSON.parse(JSON.stringify(this.version.cards)),
      source_ids: [...(this.version.source_ids || [])],
    };

    this.creatorApi.createVersion(this.lessonId, newVerPayload).subscribe({
      next: (created) => {
        this.versions.push(created);
        this.version = created;
        this.selectedCardIndex = 0;
        this.saveState = 'saved';
        this.saveMessage = 'New draft revision created!';
        this.isLoading = false;
        this.runValidation();
        this.cdr.markForCheck();
        setTimeout(() => {
          this.saveMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      },
      error: (err: any) => {
        this.isLoading = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to create new revision.';
        this.cdr.markForCheck();
      },
    });
  }

  loadSources(): void {
    this.creatorApi.getSources().subscribe({
      next: (sources) => {
        this.availableSources = sources;
        this.cdr.markForCheck();
      },
      error: () => {},
    });
  }

  // --- Active Card Selection ---

  get activeCard(): CreatorCard | null {
    if (!this.version || !this.version.cards || this.version.cards.length === 0) {
      return null;
    }
    if (this.selectedCardIndex >= this.version.cards.length) {
      this.selectedCardIndex = this.version.cards.length - 1;
    }
    return this.version.cards[this.selectedCardIndex] || null;
  }

  selectCard(index: number): void {
    if (!this.version) return;
    if (index >= 0 && index < this.version.cards.length) {
      this.selectedCardIndex = index;
      this.cdr.markForCheck();
    }
  }

  markUnsaved(): void {
    if (this.saveState !== 'saving') {
      this.saveState = 'unsaved';
    }
    this.runValidation();
  }

  // --- Card CRUD & Sequencing ---

  addCard(type: 'explanation' | 'interaction' | 'recap'): void {
    if (!this.version) return;
    const pos = this.version.cards.length;
    const newCard: CreatorCard = {
      id: `card-${Date.now()}`,
      position: pos,
      card_type: type,
      content_blocks:
        type === 'explanation'
          ? [
              { block_type: 'heading', body: `Concept ${pos + 1}` },
              { block_type: 'text', body: '' },
            ]
          : type === 'recap'
          ? [
              { block_type: 'heading', body: 'Chapter Summary & Key Takeaways' },
              { block_type: 'text', body: '' },
            ]
          : [{ block_type: 'text', body: 'Answer the question below to verify your understanding.' }],
      source_ids: [],
      interaction: type === 'interaction' ? this.createDefaultQuiz() : null,
    };

    this.version.cards.push(newCard);
    this.selectedCardIndex = this.version.cards.length - 1;
    this.markUnsaved();
  }

  duplicateCard(index: number): void {
    if (!this.version) return;
    const sourceCard = this.version.cards[index];
    if (!sourceCard) return;

    // Deep clone card
    const clonedCard: CreatorCard = JSON.parse(JSON.stringify(sourceCard));
    clonedCard.id = `card-${Date.now()}`;
    clonedCard.position = index + 1;

    this.version.cards.splice(index + 1, 0, clonedCard);
    this.version.cards.forEach((c, i) => (c.position = i));
    this.selectedCardIndex = index + 1;
    this.markUnsaved();
  }

  removeCard(index: number): void {
    if (!this.version) return;
    if (this.version.cards.length <= 1) {
      this.errorMessage = 'A chapter must contain at least one content card.';
      return;
    }

    this.version.cards.splice(index, 1);
    this.version.cards.forEach((c, i) => (c.position = i));
    if (this.selectedCardIndex >= this.version.cards.length) {
      this.selectedCardIndex = this.version.cards.length - 1;
    }
    this.markUnsaved();
  }

  moveCard(index: number, direction: -1 | 1): void {
    if (!this.version) return;
    const targetIdx = index + direction;
    if (targetIdx < 0 || targetIdx >= this.version.cards.length) return;

    const cards = this.version.cards;
    [cards[index], cards[targetIdx]] = [cards[targetIdx], cards[index]];
    cards.forEach((c, i) => (c.position = i));
    this.selectedCardIndex = targetIdx;
    this.markUnsaved();
  }

  setCardType(card: CreatorCard, newType: 'explanation' | 'interaction' | 'recap'): void {
    if (card.card_type === newType) return;
    card.card_type = newType;
    if (newType === 'interaction' && !card.interaction) {
      card.interaction = this.createDefaultQuiz();
    }
    this.markUnsaved();
  }

  createDefaultQuiz(): CreatorInteraction {
    return {
      interaction_type: 'single_choice',
      question_prompt: '',
      incorrect_behaviour: 'retry',
      options: [
        {
          id: `opt-${Date.now()}-1`,
          label: '',
          is_correct: true,
          feedback: 'Correct! That is scientifically accurate.',
        },
        {
          id: `opt-${Date.now()}-2`,
          label: '',
          is_correct: false,
          feedback: 'Not quite. Review the explanation card and try again.',
        },
      ],
    };
  }

  // --- Content Blocks in Card ---

  addContentBlock(card: CreatorCard, type: 'text' | 'heading'): void {
    card.content_blocks.push({ block_type: type, body: '' });
    this.markUnsaved();
  }

  removeContentBlock(card: CreatorCard, blockIdx: number): void {
    if (card.content_blocks.length <= 1 && card.card_type !== 'interaction') {
      return;
    }
    card.content_blocks.splice(blockIdx, 1);
    this.markUnsaved();
  }

  // --- Quiz Options Management ---

  addQuizOption(interaction: CreatorInteraction): void {
    interaction.options.push({
      id: `opt-${Date.now()}`,
      label: '',
      is_correct: false,
      feedback: 'Review the guidance above and reconsider your choice.',
    });
    this.markUnsaved();
  }

  removeQuizOption(interaction: CreatorInteraction, optIndex: number): void {
    if (interaction.options.length <= 2) {
      this.errorMessage = 'A multiple-choice question must have at least 2 answer options.';
      return;
    }
    const wasCorrect = interaction.options[optIndex].is_correct;
    interaction.options.splice(optIndex, 1);
    if (wasCorrect && interaction.options.length > 0) {
      interaction.options[0].is_correct = true;
    }
    this.markUnsaved();
  }

  setCorrectQuizOption(interaction: CreatorInteraction, selectedIndex: number): void {
    interaction.options.forEach((opt, idx) => {
      opt.is_correct = idx === selectedIndex;
    });
    this.markUnsaved();
  }

  // --- Medical Sources ---

  isSourceAttached(sourceId: string): boolean {
    if (!this.version) return false;
    return this.version.source_ids.includes(sourceId);
  }

  toggleAttachSource(sourceId: string): void {
    if (!this.version) return;
    const idx = this.version.source_ids.indexOf(sourceId);
    if (idx >= 0) {
      this.version.source_ids.splice(idx, 1);
    } else {
      this.version.source_ids.push(sourceId);
    }
    this.markUnsaved();
  }

  openAddSourceModal(): void {
    this.newSourceTitle = '';
    this.newSourcePublisher = '';
    this.newSourceUrl = '';
    this.newSourceJurisdiction = 'Global / WHO';
    this.showAddSourceModal = true;
  }

  closeAddSourceModal(): void {
    this.showAddSourceModal = false;
  }

  createSource(): void {
    if (!this.newSourceTitle.trim() || !this.newSourceUrl.trim() || !this.newSourcePublisher.trim()) {
      this.errorMessage = 'Source title, publisher, and valid URL are required.';
      return;
    }

    this.isAddingSource = true;
    const slug = this.newSourceTitle
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 20);
    const sourceId = `src-${slug || 'health'}-${Date.now().toString().slice(-4)}`;

    this.creatorApi
      .createSource({
        id: sourceId,
        title: this.newSourceTitle.trim(),
        publisher: this.newSourcePublisher.trim(),
        url: this.newSourceUrl.trim(),
        jurisdiction: this.newSourceJurisdiction.trim() || null,
      })
      .subscribe({
        next: (created) => {
          this.availableSources.push(created);
          if (this.version) {
            this.version.source_ids.push(created.id);
            this.markUnsaved();
          }
          this.isAddingSource = false;
          this.showAddSourceModal = false;
          this.saveMessage = `Source "${created.title}" attached!`;
          this.cdr.markForCheck();
        },
        error: (err: any) => {
          this.isAddingSource = false;
          this.errorMessage = err?.error?.error?.message || 'Failed to create medical source.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Real-time Validation ---

  runValidation(): void {
    const errors: string[] = [];
    if (!this.version) return;

    if (!this.version.title?.trim()) {
      errors.push('Chapter title is empty.');
    }
    if (!this.version.cards || this.version.cards.length === 0) {
      errors.push('Chapter must have at least one card.');
    }

    this.version.cards.forEach((card, idx) => {
      const cardNum = idx + 1;
      if (card.card_type === 'interaction') {
        if (!card.interaction?.question_prompt?.trim()) {
          errors.push(`Card ${cardNum}: Quiz question prompt is empty.`);
        }
        if (!card.interaction?.options || card.interaction.options.length < 2) {
          errors.push(`Card ${cardNum}: Quiz must have at least 2 options.`);
        } else {
          const correctCount = card.interaction.options.filter((o) => o.is_correct).length;
          if (correctCount !== 1) {
            errors.push(`Card ${cardNum}: Exactly one correct answer must be selected.`);
          }
          const hasEmptyOption = card.interaction.options.some((o) => !o.label?.trim());
          if (hasEmptyOption) {
            errors.push(`Card ${cardNum}: All quiz choices must have text.`);
          }
        }
      }
    });

    this.validationErrors = errors;
  }

  // --- Save & Workflow ---

  saveDraft(): void {
    if (!this.version) return;
    this.saveState = 'saving';
    this.errorMessage = '';
    this.saveMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.updateVersion(this.version.id, this.version).subscribe({
      next: (updated) => {
        this.version = updated;
        this.saveState = 'saved';
        this.saveMessage = 'Draft saved successfully!';
        this.runValidation();
        this.cdr.markForCheck();
        setTimeout(() => {
          this.saveMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      },
      error: (err: any) => {
        this.saveState = 'error';
        this.errorMessage = err?.error?.error?.message || 'Failed to save changes.';
        this.cdr.markForCheck();
      },
    });
  }

  openSubmitModal(): void {
    this.runValidation();
    this.showSubmitModal = true;
  }

  closeSubmitModal(): void {
    this.showSubmitModal = false;
  }

  confirmSubmitForReview(): void {
    if (!this.version) return;
    if (this.validationErrors.length > 0) {
      this.errorMessage = 'Please resolve all validation errors before submitting for review.';
      this.showSubmitModal = false;
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    // First save any pending changes, then submit
    this.creatorApi.updateVersion(this.version.id, this.version).subscribe({
      next: () => {
        this.creatorApi.submitForReview(this.version!.id).subscribe({
          next: (submitted) => {
            this.version = submitted;
            this.isSubmitting = false;
            this.showSubmitModal = false;
            this.saveState = 'saved';
            this.saveMessage = 'Chapter successfully submitted for peer review!';
            this.cdr.markForCheck();
          },
          error: (err: any) => {
            this.isSubmitting = false;
            this.errorMessage = err?.error?.error?.message || 'Failed to submit for review.';
            this.cdr.markForCheck();
          },
        });
      },
      error: (err: any) => {
        this.isSubmitting = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to save prior to submission.';
        this.cdr.markForCheck();
      },
    });
  }

  previewChapter(): void {
    if (this.version) {
      this.router.navigate(['/creator/preview', this.version.id]);
    }
  }

  getCardSummary(card: CreatorCard): string {
    if (card.card_type === 'explanation') {
      const heading = card.content_blocks.find((b) => b.block_type === 'heading');
      if (heading?.body) return heading.body;
      const text = card.content_blocks.find((b) => b.block_type === 'text');
      return text?.body ? text.body.substring(0, 32) + '…' : 'Explanation Card';
    }
    if (card.card_type === 'interaction') {
      return card.interaction?.question_prompt
        ? card.interaction.question_prompt.substring(0, 32) + '…'
        : 'Multiple Choice Quiz';
    }
    return 'Chapter Recap & Summary';
  }
}
