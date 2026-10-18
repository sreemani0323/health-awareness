import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LessonPlayerComponent } from './lesson-player.component';
import { ApiService } from '../../services/api.service';
import { LessonDetail } from '../../models/api.models';

describe('LessonPlayerComponent', () => {
  const mockLesson: LessonDetail = {
    id: 'lesson-1',
    topic_id: 'topic-hygiene',
    version_id: 'ver-1',
    version_number: 1,
    title: 'Effective Handwashing Steps',
    summary: 'Master the 20-second handwashing technique',
    language: 'en',
    learning_objectives: ['Wash hands for 20 seconds', 'Identify when to use soap'],
    estimated_duration_minutes: 4,
    sources: [
      {
        id: 'src-1',
        title: 'CDC Handwashing Guidelines',
        publisher: 'Centers for Disease Control and Prevention',
        url: 'https://www.cdc.gov/handwashing',
        publication_date: '2024-01-01',
        access_date: '2024-06-01',
        jurisdiction: 'Global',
      },
    ],
    cards: [
      {
        id: 'card-1',
        position: 1,
        card_type: 'explanation',
        content_blocks: [
          { block_type: 'heading', body: 'Why Handwashing Matters' },
          { block_type: 'text', body: 'Washing your hands with soap removes germs and saves lives.' },
        ],
        source_ids: ['src-1'],
        interaction: null,
      },
      {
        id: 'card-2',
        position: 2,
        card_type: 'interaction',
        content_blocks: [
          { block_type: 'heading', body: 'Knowledge Check' },
        ],
        source_ids: ['src-1'],
        interaction: {
          interaction_type: 'single_choice',
          question_prompt: 'How long should you scrub hands with soap?',
          incorrect_behaviour: 'retry',
          options: [
            { id: 'opt-1', label: '5 seconds', is_correct: false, feedback: '5 seconds is too short.' },
            { id: 'opt-2', label: 'At least 20 seconds', is_correct: true, feedback: 'Correct! 20 seconds is recommended.' },
          ],
        },
      },
      {
        id: 'card-3',
        position: 3,
        card_type: 'recap',
        content_blocks: [
          { block_type: 'heading', body: 'Key Takeaways' },
          { block_type: 'text', body: 'Always use soap and clean water.' },
        ],
        source_ids: [],
        interaction: null,
      },
    ],
  };

  let mockApiService: {
    getLessonDetail: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    mockApiService = {
      getLessonDetail: vi.fn().mockReturnValue(of(mockLesson)),
    };

    await TestBed.configureTestingModule({
      imports: [LessonPlayerComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'lessonId' ? 'lesson-1' : null),
              },
            },
          },
        },
        { provide: ApiService, useValue: mockApiService },
      ],
    }).compileComponents();
  });

  it('should create the lesson player', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should load lesson detail and initialize on card 1', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.lesson()).toBeTruthy();
    expect(component.totalCards()).toBe(3);
    expect(component.currentCardIndex()).toBe(0);
    expect(component.isFirstCard()).toBe(true);
    expect(component.isLastCard()).toBe(false);
    expect(component.progressPercent()).toBe(33);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.lesson-header__title')?.textContent).toBe('Effective Handwashing Steps');
    expect(compiled.querySelector('.card-heading')?.textContent).toBe('Why Handwashing Matters');
  });

  it('should navigate to next card on explanation card', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.canProceed()).toBe(true);
    component.nextCard();
    fixture.detectChanges();

    expect(component.currentCardIndex()).toBe(1);
    expect(component.isFirstCard()).toBe(false);
    expect(component.currentCard()?.card_type).toBe('interaction');
  });

  it('should require answering quiz before proceeding on interaction card', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    // Move to quiz card
    component.goToCard(1);
    fixture.detectChanges();

    // Cannot proceed before answering
    expect(component.canProceed()).toBe(false);

    // Select option 2 (correct)
    component.selectOption('opt-2');
    expect(component.selectedOptionId()).toBe('opt-2');

    // Submit answer
    component.submitAnswer();
    fixture.detectChanges();

    expect(component.answerSubmitted()).toBe(true);
    expect(component.answerCorrect()).toBe(true);
    expect(component.feedbackText()).toContain('20 seconds is recommended');
    expect(component.canProceed()).toBe(true);
  });

  it('should toggle source references panel', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.showSources()).toBe(false);
    component.toggleSources();
    expect(component.showSources()).toBe(true);

    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.sources-panel')).toBeTruthy();
    expect(compiled.querySelector('.source-item__link')?.textContent).toContain('CDC Handwashing Guidelines');
  });

  it('should show finish button on last card', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.goToCard(2);
    fixture.detectChanges();

    expect(component.isLastCard()).toBe(true);
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#finish-lesson-btn')).toBeTruthy();
    expect(compiled.querySelector('#lesson-completion-card')).toBeTruthy();
  });

  it('should handle API load failure gracefully', () => {
    mockApiService.getLessonDetail.mockReturnValue(throwError(() => new Error('API failure')));
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.error()).toContain('Unable to load this lesson');
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.error-state')).toBeTruthy();
  });

  it('should track and persist learning progress on card navigation', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    const progressService = component.progressService;

    expect(progressService.hasResume()).toBe(true);
    expect(progressService.resumeState()?.lessonId).toBe('lesson-1');
    expect(progressService.resumeState()?.cardIndex).toBe(0);

    component.nextCard();
    expect(progressService.resumeState()?.cardIndex).toBe(1);
  });

  it('should mark lesson completed when finishing the lesson', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    const progressService = component.progressService;

    component.goToCard(2);
    fixture.detectChanges();

    expect(progressService.isLessonCompleted('lesson-1')).toBe(false);

    component.onCompleteLesson();
    expect(progressService.isLessonCompleted('lesson-1')).toBe(true);
  });

  it('should allow sharing the lesson link', async () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    await component.shareLesson();
    expect(component.shareToastMessage()).toBeTruthy();
    fixture.detectChanges();

    const toast = fixture.nativeElement.querySelector('#share-toast-msg');
    expect(toast).toBeTruthy();
  });

  it('should render and toggle practical activity takeaway on the completion card', () => {
    const fixture = TestBed.createComponent(LessonPlayerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.goToCard(2);
    fixture.detectChanges();

    const takeaway = fixture.nativeElement.querySelector('#completion-practical-takeaway');
    expect(takeaway).toBeTruthy();

    const act = component.associatedActivity();
    expect(act).toBeTruthy();
    if (act) {
      expect(component.isActivityCompleted(act.id)).toBe(false);
      component.toggleActivity(act.id);
      expect(component.isActivityCompleted(act.id)).toBe(true);
    }
  });
});
