import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../../services/creator-api.service';
import { CreatorTopic, CreatorLesson } from '../../../models/creator.models';
import { CreatorNavbarComponent } from '../../../components/creator-navbar/creator-navbar.component';

@Component({
  selector: 'app-topic-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CreatorNavbarComponent],
  templateUrl: './topic-editor.html',
  styleUrl: './topic-editor.css',
})
export class TopicEditor implements OnInit {
  isNewTopic = false;
  topicId = '';
  topic: Partial<CreatorTopic> = {
    id: '',
    title: '',
    slug: '',
    description: '',
    display_order: 0,
    status: 'draft',
    cover_image_ref: null,
    cover_image_alt: null,
  };

  // Additional guided creation fields
  category = 'general';
  targetAudience = 'all';
  language = 'en';

  lessons: CreatorLesson[] = [];
  isLoading = true;
  isSaving = false;
  saveMessage = '';
  errorMessage = '';

  // Topic Metadata Edit modal/drawer
  showTopicDetailsModal = false;

  // Add Chapter modal
  showAddChapterModal = false;
  newChapterTitle = '';
  newChapterSummary = '';
  isAddingChapter = false;

  // Delete Chapter Confirmation modal
  chapterToDelete: CreatorLesson | null = null;
  isDeletingChapter = false;

  // Slug customization
  isCustomSlug = false;

  constructor(
    public creatorApi: CreatorApiService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      this.topicId = params.get('topicId') || '';
      this.isNewTopic = !this.topicId || this.topicId === 'new';

      if (!this.isNewTopic) {
        this.loadTopic();
        this.loadLessons();
      } else {
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadTopic(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.getTopic(this.topicId).subscribe({
      next: (topic) => {
        this.topic = topic;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        if (err?.status === 401) {
          this.router.navigate(['/creator/login']);
          return;
        }
        this.errorMessage = 'Failed to load topic details.';
        this.isLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  loadLessons(): void {
    this.creatorApi.getTopicLessons(this.topicId).subscribe({
      next: (lessons) => {
        // Sort explicitly by display_order
        this.lessons = lessons.sort((a, b) => a.display_order - b.display_order);
        this.cdr.markForCheck();
      },
      error: () => {
        this.cdr.markForCheck();
      },
    });
  }

  onTitleChange(): void {
    if (!this.isCustomSlug && this.topic.title) {
      this.topic.slug = this.topic.title
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
    }
  }

  toggleCustomSlug(): void {
    this.isCustomSlug = true;
  }

  // --- Topic Creation & Saving ---

  saveTopic(): void {
    if (!this.topic.title?.trim()) {
      this.errorMessage = 'Topic title is required.';
      return;
    }
    if (!this.topic.description?.trim()) {
      this.errorMessage = 'Topic description is required.';
      return;
    }

    this.isSaving = true;
    this.saveMessage = '';
    this.errorMessage = '';
    this.cdr.markForCheck();

    if (this.isNewTopic) {
      if (!this.topic.slug) {
        this.onTitleChange();
      }
      // Generate clean internal ID based on slug
      const slug = this.topic.slug || 'health-topic';
      const generatedId = `topic-${slug}`.substring(0, 60);

      const newTopicPayload: Partial<CreatorTopic> = {
        id: generatedId,
        title: this.topic.title.trim(),
        slug: slug,
        description: this.topic.description.trim(),
        display_order: this.topic.display_order || 0,
        status: 'draft',
        cover_image_ref: this.topic.cover_image_ref || null,
        cover_image_alt: this.topic.cover_image_alt || null,
      };

      this.creatorApi.createTopic(newTopicPayload).subscribe({
        next: (created) => {
          this.isSaving = false;
          this.saveMessage = 'Topic created successfully!';
          this.cdr.markForCheck();
          // Directly navigate to this topic's curriculum workspace!
          this.router.navigate(['/creator/topic', created.id]);
        },
        error: (err: any) => {
          this.isSaving = false;
          this.errorMessage = err?.error?.error?.message || 'Failed to create topic.';
          this.cdr.markForCheck();
        },
      });
    } else {
      this.creatorApi.updateTopic(this.topicId, this.topic).subscribe({
        next: (updated) => {
          this.topic = updated;
          this.isSaving = false;
          this.saveMessage = 'Topic settings saved!';
          this.showTopicDetailsModal = false;
          this.cdr.markForCheck();
          setTimeout(() => {
            this.saveMessage = '';
            this.cdr.markForCheck();
          }, 3500);
        },
        error: (err: any) => {
          this.isSaving = false;
          this.errorMessage = err?.error?.error?.message || 'Failed to save topic settings.';
          this.cdr.markForCheck();
        },
      });
    }
  }

  // --- Chapter Management ---

  openAddChapterModal(): void {
    this.newChapterTitle = '';
    this.newChapterSummary = '';
    this.showAddChapterModal = true;
  }

  closeAddChapterModal(): void {
    this.showAddChapterModal = false;
  }

  addChapter(): void {
    if (!this.newChapterTitle.trim()) {
      this.errorMessage = 'Chapter title is required.';
      return;
    }

    this.isAddingChapter = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    const titleSlug = this.newChapterTitle
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 30);
    const lessonId = `lesson-${titleSlug || 'chapter'}-${Date.now().toString().slice(-4)}`;
    const nextOrder = (Math.max(0, ...this.lessons.map(l => l.display_order)) || 0) + 1;

    this.creatorApi
      .createLesson(this.topicId, {
        id: lessonId,
        title: this.newChapterTitle.trim(),
        summary: this.newChapterSummary.trim(),
        display_order: nextOrder,
      })
      .subscribe({
        next: (created) => {
          this.lessons.push(created);
          this.lessons.sort((a, b) => a.display_order - b.display_order);
          this.isAddingChapter = false;
          this.showAddChapterModal = false;
          this.saveMessage = `Chapter "${created.title || this.newChapterTitle}" added to curriculum!`;
          this.cdr.markForCheck();
          setTimeout(() => {
            this.saveMessage = '';
            this.cdr.markForCheck();
          }, 4000);
        },
        error: (err: any) => {
          this.isAddingChapter = false;
          this.errorMessage = err?.error?.error?.message || 'Failed to create chapter.';
          this.cdr.markForCheck();
        },
      });
  }

  moveChapter(index: number, direction: -1 | 1): void {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= this.lessons.length) return;

    const currentChapter = this.lessons[index];
    const targetChapter = this.lessons[targetIndex];

    const currentOrder = currentChapter.display_order;
    const targetOrder = targetChapter.display_order;

    // Swap display_order
    currentChapter.display_order = targetOrder;
    targetChapter.display_order = currentOrder;

    // Persist current chapter's new order
    this.creatorApi.updateLesson(currentChapter.id, { display_order: targetOrder }).subscribe({
      next: () => {
        // Persist target chapter's new order
        this.creatorApi.updateLesson(targetChapter.id, { display_order: currentOrder }).subscribe({
          next: () => {
            this.lessons.sort((a, b) => a.display_order - b.display_order);
            this.cdr.markForCheck();
          },
          error: () => this.loadLessons(),
        });
      },
      error: () => this.loadLessons(),
    });
  }

  confirmDeleteChapter(chapter: CreatorLesson): void {
    this.chapterToDelete = chapter;
  }

  cancelDeleteChapter(): void {
    this.chapterToDelete = null;
  }

  deleteChapter(): void {
    if (!this.chapterToDelete) return;

    this.isDeletingChapter = true;
    this.cdr.markForCheck();

    this.creatorApi.deleteLesson(this.chapterToDelete.id).subscribe({
      next: () => {
        this.lessons = this.lessons.filter((l) => l.id !== this.chapterToDelete!.id);
        this.isDeletingChapter = false;
        this.chapterToDelete = null;
        this.saveMessage = 'Chapter removed from curriculum.';
        this.cdr.markForCheck();
        setTimeout(() => {
          this.saveMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      },
      error: (err: any) => {
        this.isDeletingChapter = false;
        this.errorMessage = err?.error?.error?.message || 'Failed to delete chapter.';
        this.chapterToDelete = null;
        this.cdr.markForCheck();
      },
    });
  }

  openChapterEditor(lesson: CreatorLesson): void {
    this.router.navigate(['/creator/lesson', lesson.id]);
  }

  previewChapter(lesson: CreatorLesson): void {
    const versionId = lesson.draft_version_id || lesson.published_version_id;
    if (versionId) {
      this.router.navigate(['/creator/preview', versionId]);
    } else {
      this.openChapterEditor(lesson);
    }
  }
}
