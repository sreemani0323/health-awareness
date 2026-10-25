import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { CreatorApiService } from '../../services/creator-api.service';
import { Login } from './login/login';
import { Dashboard } from './dashboard/dashboard';
import { TopicEditor } from './topic-editor/topic-editor';
import { LessonEditor } from './lesson-editor/lesson-editor';
import { ReviewQueue } from './review-queue/review-queue';
import { PreviewComponent } from './preview/preview';
import { CreatorNavbarComponent } from '../../components/creator-navbar/creator-navbar.component';
import { AdminWorkspaceComponent } from './admin/admin';
import { AuthUser, CreatorTopic, CreatorVersion, AdminUser, AdminOverview } from '../../models/creator.models';
import { environment } from '../../../environments/environment';

describe('Creator Studio Frontend Suite', () => {
  let apiService: CreatorApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        CreatorApiService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });

    apiService = TestBed.inject(CreatorApiService);
    httpMock = TestBed.inject(HttpTestingController);

    // Initial checkAuth request in constructor
    const meReq = httpMock.match(`${environment.apiBaseUrl}/auth/me`);
    if (meReq.length > 0) {
      meReq[0].flush({ error: { code: 'UNAUTHORIZED' } }, { status: 401, statusText: 'Unauthorized' });
    }
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should initialize CreatorApiService and handle unauthenticated state', () => {
    expect(apiService).toBeTruthy();
    expect(apiService.isAuthenticated).toBe(false);
    expect(apiService.currentUser).toBeNull();
  });

  it('should authenticate user and update currentUser$ signal on login', () => {
    const mockUser: AuthUser = {
      user_id: 'user-contributor',
      username: 'contributor',
      display_name: 'Health Contributor',
      role: 'contributor',
    };

    let emission: AuthUser | null = null;
    apiService.currentUser$.subscribe((u: AuthUser | null) => (emission = u));

    apiService.login({ username: 'contributor', password: 'password123' }).subscribe((res) => {
      expect(res.username).toBe('contributor');
      expect(res.role).toBe('contributor');
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.withCredentials).toBe(true);
    req.flush({ data: mockUser, meta: {} });

    expect(apiService.isAuthenticated).toBe(true);
    expect(apiService.currentUser?.username).toBe('contributor');
    expect((emission as AuthUser | null)?.role).toBe('contributor');
  });

  it('should clear auth state on logout', () => {
    apiService.logout().subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/auth/logout`);
    expect(req.request.method).toBe('POST');
    req.flush({ data: { message: 'Logged out' }, meta: {} });

    expect(apiService.isAuthenticated).toBe(false);
    expect(apiService.currentUser).toBeNull();
  });

  it('should fetch topics list via CreatorApiService', () => {
    const mockTopics: CreatorTopic[] = [
      {
        id: 'topic-hygiene',
        title: 'Personal Hygiene',
        slug: 'personal-hygiene',
        description: 'Cleanliness education',
        display_order: 1,
        status: 'published',
        cover_image_ref: null,
        cover_image_alt: null,
      },
    ];

    apiService.getTopics().subscribe((topics) => {
      expect(topics.length).toBe(1);
      expect(topics[0].id).toBe('topic-hygiene');
      expect(topics[0].status).toBe('published');
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/creator/topics`);
    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBe(true);
    req.flush({ data: mockTopics, meta: {} });
  });

  it('should create LoginComponent and instantiate correctly', () => {
    const fixture = TestBed.createComponent(Login);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.username).toBe('');
    expect(comp.isLoading).toBe(false);
  });

  it('should create Dashboard component and categorize topics by status', () => {
    const fixture = TestBed.createComponent(Dashboard);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();

    comp.topics = [
      { id: 't1', title: 'T1', slug: 't1', description: 'desc', display_order: 1, status: 'published', cover_image_ref: null, cover_image_alt: null, chapterCount: 2, inReviewCount: 0, changesRequestedCount: 0 },
      { id: 't2', title: 'T2', slug: 't2', description: 'desc', display_order: 2, status: 'draft', cover_image_ref: null, cover_image_alt: null, chapterCount: 1, inReviewCount: 0, changesRequestedCount: 1, latestFeedback: 'Fix quiz answer' },
    ];

    expect(comp.publishedTopics.length).toBe(1);
    expect(comp.draftTopics.length).toBe(1);
    expect(comp.totalChangesRequestedCount).toBe(1);
    expect(comp.attentionTopicsCount).toBe(1);

    comp.selectedTab = 'attention';
    expect(comp.filteredTopics.length).toBe(1);
    expect(comp.filteredTopics[0].id).toBe('t2');
    expect(comp.getNextActionLabel(comp.topics[1])).toBe('Address Review Feedback');
  });

  it('should create ReviewQueue component and support queue inspection', () => {
    const fixture = TestBed.createComponent(ReviewQueue);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.items.length).toBe(0);
    expect(comp.isSubmittingDecision).toBe(false);

    const mockVersions: CreatorVersion[] = [
      {
        id: 'ver-test',
        lesson_id: 'lesson-test',
        version_number: 1,
        title: 'Test Lesson',
        summary: 'Test summary',
        language: 'en',
        learning_objectives: ['Learn A'],
        estimated_duration_minutes: 5,
        status: 'submitted_for_review',
        cards: [],
        source_ids: [],
        review_feedback: 'Needs additional source reference',
      },
    ];

    fixture.detectChanges();
    const queueReq = httpMock.expectOne(`${environment.apiBaseUrl}/creator/reviews`);
    queueReq.flush({ data: mockVersions, meta: {} });

    expect(comp.items.length).toBe(1);
    expect(comp.items[0].title).toBe('Test Lesson');
    expect(comp.items[0].review_feedback).toBe('Needs additional source reference');
  });

  it('should create PreviewComponent and correctly compute card navigation', () => {
    const fixture = TestBed.createComponent(PreviewComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.totalCards()).toBe(0);
    expect(comp.isFirstCard()).toBe(true);
    expect(comp.progressPercent()).toBe(0);
  }, 15000);

  it('should create CreatorNavbarComponent and render user role correctly', () => {
    const fixture = TestBed.createComponent(CreatorNavbarComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.currentSection).toBe('dashboard');

    comp.currentUser = {
      user_id: 'user-admin-1',
      username: 'admin',
      display_name: 'Lead Health Director',
      role: 'admin',
    };
    expect(comp.canReview).toBe(true);
    expect(comp.canCreate).toBe(true);
    expect(comp.isAdmin).toBe(true);
  });

  it('should create TopicEditor component and auto-generate slug from title', () => {
    const fixture = TestBed.createComponent(TopicEditor);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    comp.isNewTopic = true;
    comp.topic.title = 'Clean Water Access & Filtration';
    comp.onTitleChange();
    expect(comp.topic.slug).toBe('clean-water-access-filtration');
  });

  it('should create LessonEditor component and validate quiz interactions', () => {
    const fixture = TestBed.createComponent(LessonEditor);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.saveState).toBe('saved');

    // Add quiz card and test validation
    comp.version = {
      id: 'ver-test',
      lesson_id: 'lesson-test',
      version_number: 1,
      title: 'Water Purification',
      summary: 'Boiling and filtering',
      language: 'en',
      learning_objectives: ['Learn filtration'],
      estimated_duration_minutes: 5,
      status: 'draft',
      cards: [
        {
          id: 'card-1',
          position: 0,
          card_type: 'interaction',
          content_blocks: [],
          source_ids: [],
          interaction: {
            interaction_type: 'single_choice',
            question_prompt: '',
            incorrect_behaviour: 'retry',
            options: [
              { id: 'opt-1', label: 'Boiling', is_correct: true, feedback: 'Correct!' },
              { id: 'opt-2', label: 'Freezing', is_correct: false, feedback: 'Try again' },
            ],
          },
        },
      ],
      source_ids: [],
    };

    comp.runValidation();
    expect(comp.validationErrors.length).toBeGreaterThan(0);
    expect(comp.validationErrors[0]).toContain('Quiz question prompt is empty');

    // Fill prompt and verify error resolves
    comp.version.cards[0].interaction!.question_prompt = 'What is the best household method?';
    comp.runValidation();
    expect(comp.validationErrors.length).toBe(0);
  });

  it('should create AdminWorkspaceComponent and filter users by role and search', () => {
    const fixture = TestBed.createComponent(AdminWorkspaceComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.activeTab).toBe('overview');

    comp.users = [
      { user_id: 'u1', username: 'admin', display_name: 'Admin User', role: 'admin', is_active: true, created_at: '2026-01-01T00:00:00Z' },
      { user_id: 'u2', username: 'rev1', display_name: 'Dr. Reviewer', role: 'reviewer', is_active: true, created_at: '2026-01-01T00:00:00Z' },
      { user_id: 'u3', username: 'cont1', display_name: 'Community Author', role: 'contributor', is_active: false, created_at: '2026-01-01T00:00:00Z' },
    ];

    expect(comp.totalUsersCount).toBe(3);
    expect(comp.activeUsersCount).toBe(2);

    comp.roleFilter = 'reviewer';
    expect(comp.filteredUsers.length).toBe(1);
    expect(comp.filteredUsers[0].username).toBe('rev1');

    comp.roleFilter = 'all';
    comp.userSearch = 'Community';
    expect(comp.filteredUsers.length).toBe(1);
    expect(comp.filteredUsers[0].username).toBe('cont1');
  });
});
