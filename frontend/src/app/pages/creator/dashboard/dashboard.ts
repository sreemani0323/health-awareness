import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CreatorApiService } from '../../../services/creator-api.service';
import { CreatorTopic, AuthUser } from '../../../models/creator.models';
import { CreatorNavbarComponent } from '../../../components/creator-navbar/creator-navbar.component';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface TopicWithMetadata extends CreatorTopic {
  chapterCount: number;
  inReviewCount: number;
  changesRequestedCount: number;
  latestFeedback?: string | null;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, CreatorNavbarComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  topics: TopicWithMetadata[] = [];
  currentUser: AuthUser | null = null;
  isLoading = true;
  errorMessage = '';

  // Filter & Search state
  selectedTab: 'all' | 'drafts' | 'attention' | 'submitted' | 'published' = 'all';
  searchQuery = '';

  constructor(
    public creatorApi: CreatorApiService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.creatorApi.currentUser$.subscribe((user) => {
      this.currentUser = user;
      this.cdr.markForCheck();
    });

    this.route.queryParams.subscribe((params) => {
      const tab = params['tab'];
      if (
        tab === 'drafts' ||
        tab === 'attention' ||
        tab === 'submitted' ||
        tab === 'published' ||
        tab === 'all'
      ) {
        this.selectedTab = tab;
      } else {
        this.selectedTab = 'all';
      }
      this.cdr.markForCheck();
    });

    this.loadTopics();
  }

  loadTopics(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.getTopics().subscribe({
      next: (topics) => {
        if (topics.length === 0) {
          this.topics = [];
          this.isLoading = false;
          this.cdr.markForCheck();
          return;
        }

        // Fetch lesson counts for each topic to display true chapter counts & feedback
        const lessonRequests = topics.map((t) =>
          this.creatorApi.getTopicLessons(t.id).pipe(catchError(() => of([])))
        );

        forkJoin(lessonRequests).subscribe({
          next: (lessonArrays) => {
            this.topics = topics.map((t, index) => {
              const lessons = lessonArrays[index] || [];
              const inReview = lessons.filter((l) => l.status === 'submitted_for_review').length;
              const changesReq = lessons.filter((l) => l.review_feedback && l.status === 'draft');
              const latestFb = changesReq.length > 0 ? changesReq[0].review_feedback : null;
              return {
                ...t,
                chapterCount: lessons.length,
                inReviewCount: inReview,
                changesRequestedCount: changesReq.length,
                latestFeedback: latestFb,
              };
            });
            this.isLoading = false;
            this.cdr.markForCheck();
          },
          error: () => {
            this.topics = topics.map((t) => ({
              ...t,
              chapterCount: 0,
              inReviewCount: 0,
              changesRequestedCount: 0,
              latestFeedback: null,
            }));
            this.isLoading = false;
            this.cdr.markForCheck();
          },
        });
      },
      error: (err) => {
        this.isLoading = false;
        if (err?.status === 401) {
          this.router.navigate(['/creator/login']);
        } else {
          this.errorMessage = 'Failed to load topics. Please check connectivity.';
        }
        this.cdr.markForCheck();
      },
    });
  }

  get filteredTopics(): TopicWithMetadata[] {
    return this.topics.filter((topic) => {
      // Tab filter
      if (this.selectedTab === 'attention' && topic.changesRequestedCount === 0) {
        return false;
      }
      if (this.selectedTab === 'drafts' && topic.status !== 'draft') {
        return false;
      }
      if (this.selectedTab === 'published' && topic.status !== 'published') {
        return false;
      }
      if (this.selectedTab === 'submitted') {
        // Shown if topic itself is submitted or has chapters in review
        if (topic.status !== 'draft' && topic.inReviewCount === 0) {
          return false;
        }
      }

      // Search filter
      if (this.searchQuery.trim()) {
        const q = this.searchQuery.toLowerCase();
        const matchesTitle = topic.title?.toLowerCase().includes(q);
        const matchesDesc = topic.description?.toLowerCase().includes(q);
        const matchesSlug = topic.slug?.toLowerCase().includes(q);
        if (!matchesTitle && !matchesDesc && !matchesSlug) {
          return false;
        }
      }

      return true;
    });
  }

  get draftTopics(): TopicWithMetadata[] {
    return this.topics.filter((t) => t.status === 'draft');
  }

  get publishedTopics(): TopicWithMetadata[] {
    return this.topics.filter((t) => t.status === 'published');
  }

  // Summary Metrics supported by actual loaded application data
  get totalTopicsCount(): number {
    return this.topics.length;
  }

  get draftCount(): number {
    return this.topics.filter((t) => t.status === 'draft').length;
  }

  get publishedCount(): number {
    return this.topics.filter((t) => t.status === 'published').length;
  }

  get totalChaptersCount(): number {
    return this.topics.reduce((acc, t) => acc + t.chapterCount, 0);
  }

  get totalChangesRequestedCount(): number {
    return this.topics.reduce((acc, t) => acc + (t.changesRequestedCount || 0), 0);
  }

  get attentionTopicsCount(): number {
    return this.topics.filter((t) => t.changesRequestedCount > 0).length;
  }

  setTab(tab: 'all' | 'drafts' | 'attention' | 'submitted' | 'published'): void {
    this.selectedTab = tab;
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: tab === 'all' ? null : tab },
      queryParamsHandling: 'merge',
    });
  }

  createNewTopic(): void {
    this.router.navigate(['/creator/topic/new']);
  }

  getNextActionLabel(topic: TopicWithMetadata): string {
    if (topic.changesRequestedCount > 0) {
      return 'Address Review Feedback';
    }
    if (topic.status === 'draft') {
      return topic.chapterCount === 0 ? 'Add First Chapter' : 'Continue Curriculum Authoring';
    }
    if (topic.inReviewCount > 0) {
      return 'Track Review Status';
    }
    return 'View Curriculum Outline';
  }
}
