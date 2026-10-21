import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';
import { TopicLessonsComponent } from './topic-lessons.component';
import { ApiService } from '../../services/api.service';
import { Topic, LessonSummary } from '../../models/api.models';

describe('TopicLessonsComponent', () => {
  const mockTopic: Topic = {
    id: 'topic-hygiene',
    title: 'Personal Hygiene & Handwashing',
    slug: 'hygiene',
    description: 'Learn critical hand hygiene steps',
    display_order: 1,
    cover_image_ref: null,
    cover_image_alt: null,
  };

  const mockLessons: LessonSummary[] = [
    {
      id: 'lesson-handwashing',
      topic_id: 'topic-hygiene',
      title: 'When and How to Wash Hands',
      summary: 'CDC and WHO guidelines on hand hygiene',
      language: 'en',
      estimated_duration_minutes: 5,
      published_version_id: 'v-1',
      display_order: 1,
    },
    {
      id: 'lesson-sanitizer',
      topic_id: 'topic-hygiene',
      title: 'Alcohol-Based Hand Rubs',
      summary: 'Proper sanitizer usage',
      language: 'en',
      estimated_duration_minutes: 3,
      published_version_id: 'v-2',
      display_order: 2,
    },
  ];

  let mockApiService: {
    getTopics: ReturnType<typeof vi.fn>;
    getTopicLessons: ReturnType<typeof vi.fn>;
    getTopicMastery: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    mockApiService = {
      getTopics: vi.fn().mockReturnValue(of([mockTopic])),
      getTopicLessons: vi.fn().mockReturnValue(of(mockLessons)),
      getTopicMastery: vi.fn().mockReturnValue(of(null)),
    };

    await TestBed.configureTestingModule({
      imports: [TopicLessonsComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'topicId' ? 'topic-hygiene' : null),
              },
            },
          },
        },
        { provide: ApiService, useValue: mockApiService },
      ],
    }).compileComponents();
  });

  it('should create the component', () => {
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should fetch and display topic metadata and lessons', () => {
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.topicTitle()).toBe('Personal Hygiene & Handwashing');
    expect(component.lessons().length).toBe(2);
    expect(component.loading()).toBe(false);

    const compiled = fixture.nativeElement as HTMLElement;
    const lessonItems = compiled.querySelectorAll('.lesson-item');
    expect(lessonItems.length).toBe(2);
    expect(lessonItems[0].textContent).toContain('When and How to Wash Hands');
  });

  it('should render expected learning outcomes for the topic', () => {
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const outcomesSection = compiled.querySelector('#topic-outcomes-section');
    expect(outcomesSection).toBeTruthy();
    expect(compiled.querySelector('#outcomes-heading')?.textContent).toContain(
      'Expected Learning Outcomes'
    );
    const outcomeItems = compiled.querySelectorAll('.outcome-item');
    expect(outcomeItems.length).toBeGreaterThan(0);
    expect(outcomeItems[0].textContent).toContain('20-second');
  });

  it('should show empty state when topic has no lessons', () => {
    mockApiService.getTopicLessons.mockReturnValue(of([]));
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const emptyState = compiled.querySelector('.empty-state');
    expect(emptyState).toBeTruthy();
    expect(emptyState?.textContent).toContain('No Lessons Yet');
  });

  it('should show error state when API fails', () => {
    mockApiService.getTopicLessons.mockReturnValue(throwError(() => new Error('Failed')));
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const errorState = compiled.querySelector('.error-state');
    expect(errorState).toBeTruthy();
    expect(errorState?.textContent).toContain('Unable to load lessons');
  });

  it('should render and toggle topic practical family activity', () => {
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    const activityCard = fixture.nativeElement.querySelector('#topic-family-activity');
    expect(activityCard).toBeTruthy();
    expect(activityCard.textContent).toContain('5-Step Handwashing Routine');

    const toggleBtn = fixture.nativeElement.querySelector('#topic-toggle-act-handwashing-practice') as HTMLButtonElement;
    expect(toggleBtn).toBeTruthy();
    expect(toggleBtn.textContent).toContain('Mark as Practiced Today');

    toggleBtn.click();
    fixture.detectChanges();

    expect(component.isActivityCompleted('act-handwashing-practice')).toBe(true);
    expect(toggleBtn.textContent).toContain('Practiced with Family');
  });

  it('should display completed badge and Review Lesson button for completed lessons', () => {
    const fixture = TestBed.createComponent(TopicLessonsComponent);
    const component = fixture.componentInstance;
    component.progressService.markLessonCompleted('lesson-handwashing', 'topic-hygiene');
    fixture.detectChanges();

    const badge = fixture.nativeElement.querySelector('#completed-badge-lesson-handwashing');
    expect(badge).toBeTruthy();
    expect(badge.textContent).toContain('Completed');

    const startBtn = fixture.nativeElement.querySelector('#start-lesson-lesson-handwashing');
    expect(startBtn.textContent).toContain('Review Lesson');
  });
});
