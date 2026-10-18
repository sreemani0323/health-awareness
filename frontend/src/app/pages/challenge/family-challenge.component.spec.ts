import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FamilyChallengeComponent } from './family-challenge.component';
import { ApiService } from '../../services/api.service';
import { of, throwError } from 'rxjs';
import { provideRouter } from '@angular/router';
import { Topic, LessonSummary, LessonDetail } from '../../models/api.models';

describe('FamilyChallengeComponent', () => {
  let component: FamilyChallengeComponent;
  let fixture: ComponentFixture<FamilyChallengeComponent>;
  let apiServiceSpy: {
    getTopics: ReturnType<typeof vi.fn>;
    getTopicLessons: ReturnType<typeof vi.fn>;
    getLessonDetail: ReturnType<typeof vi.fn>;
  };

  const mockTopics: Topic[] = [
    {
      id: 'topic-hygiene',
      title: 'Personal Hygiene & Handwashing',
      slug: 'hygiene',
      description: 'Hygiene guidance',
      display_order: 1,
      cover_image_ref: null,
      cover_image_alt: null,
    },
    {
      id: 'topic-water',
      title: 'Safe Drinking Water & Sanitation',
      slug: 'water',
      description: 'Safe water guidance',
      display_order: 2,
      cover_image_ref: null,
      cover_image_alt: null,
    },
  ];

  const mockHygieneLessons: LessonSummary[] = [
    {
      id: 'lesson-handwashing',
      topic_id: 'topic-hygiene',
      title: 'Effective Handwashing Techniques',
      summary: '20-second handwashing',
      language: 'en',
      estimated_duration_minutes: 5,
      published_version_id: 'ver-1',
      display_order: 1,
    },
  ];

  const mockWaterLessons: LessonSummary[] = [
    {
      id: 'lesson-water-purification',
      topic_id: 'topic-water',
      title: 'Household Water Treatment',
      summary: 'Water treatment',
      language: 'en',
      estimated_duration_minutes: 5,
      published_version_id: 'ver-2',
      display_order: 1,
    },
  ];

  const mockHygieneDetail: LessonDetail = {
    id: 'lesson-handwashing',
    topic_id: 'topic-hygiene',
    version_id: 'ver-1',
    version_number: 1,
    title: 'Effective Handwashing Techniques',
    summary: '20-second handwashing',
    language: 'en',
    learning_objectives: ['Learn handwashing'],
    estimated_duration_minutes: 5,
    cards: [
      {
        id: 'hw-card-1',
        position: 1,
        card_type: 'explanation',
        content_blocks: [{ block_type: 'text', body: 'Intro' }],
        source_ids: [],
        interaction: null,
      },
      {
        id: 'hw-card-2',
        position: 2,
        card_type: 'interaction',
        content_blocks: [],
        source_ids: [],
        interaction: {
          interaction_type: 'single_choice',
          question_prompt: 'How long should you scrub hands with soap?',
          incorrect_behaviour: 'retry',
          options: [
            { id: 'opt-1', label: '5 seconds', is_correct: false, feedback: 'Too short!' },
            { id: 'opt-2', label: 'At least 20 seconds', is_correct: true, feedback: 'Correct!' },
          ],
        },
      },
    ],
    sources: [],
  };

  const mockWaterDetail: LessonDetail = {
    id: 'lesson-water-purification',
    topic_id: 'topic-water',
    version_id: 'ver-2',
    version_number: 1,
    title: 'Household Water Treatment',
    summary: 'Water treatment',
    language: 'en',
    learning_objectives: ['Learn water treatment'],
    estimated_duration_minutes: 5,
    cards: [
      {
        id: 'water-card-2',
        position: 1,
        card_type: 'interaction',
        content_blocks: [],
        source_ids: [],
        interaction: {
          interaction_type: 'single_choice',
          question_prompt: 'Does boiling water remove dissolved arsenic?',
          incorrect_behaviour: 'retry',
          options: [
            { id: 'opt-w1', label: 'No, boiling does not remove chemicals', is_correct: true, feedback: 'Spot on!' },
            { id: 'opt-w2', label: 'Yes, it removes everything', is_correct: false, feedback: 'Incorrect' },
          ],
        },
      },
    ],
    sources: [],
  };

  beforeEach(async () => {
    const apiMock = {
      getTopics: vi.fn().mockReturnValue(of(mockTopics)),
      getTopicLessons: vi.fn((topicId: string) => {
        if (topicId === 'topic-hygiene') return of(mockHygieneLessons);
        if (topicId === 'topic-water') return of(mockWaterLessons);
        return of([]);
      }),
      getLessonDetail: vi.fn((lessonId: string) => {
        if (lessonId === 'lesson-handwashing') return of(mockHygieneDetail);
        if (lessonId === 'lesson-water-purification') return of(mockWaterDetail);
        return of(null);
      }),
    };

    await TestBed.configureTestingModule({
      imports: [FamilyChallengeComponent],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: apiMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyChallengeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the family challenge component', () => {
    expect(component).toBeTruthy();
    expect(component.loading()).toBe(false);
    expect(component.questions().length).toBe(2);
  });

  it('should present the first question with options', () => {
    const q = component.currentQuestion();
    expect(q).toBeTruthy();
    expect(q?.prompt).toBe('How long should you scrub hands with soap?');
    expect(q?.options.length).toBe(2);
    expect(component.progressPercent()).toBe(50);
  });

  it('should handle answering correctly and show positive feedback', () => {
    component.selectOption('opt-2');
    expect(component.selectedOptionId()).toBe('opt-2');

    component.submitAnswer();
    expect(component.answerSubmitted()).toBe(true);
    expect(component.answerCorrect()).toBe(true);
    expect(component.feedbackText()).toBe('Correct!');
    expect(component.completedQuestions()).toContain('hw-card-2');
  });

  it('should handle incorrect answers and allow retry', () => {
    component.selectOption('opt-1');
    component.submitAnswer();

    expect(component.answerSubmitted()).toBe(true);
    expect(component.answerCorrect()).toBe(false);
    expect(component.feedbackText()).toBe('Too short!');

    component.retryQuestion();
    expect(component.answerSubmitted()).toBe(false);
    expect(component.selectedOptionId()).toBeNull();
  });

  it('should navigate to the next question and complete the challenge', () => {
    // Answer question 1
    component.selectOption('opt-2');
    component.submitAnswer();
    component.nextQuestion();

    expect(component.currentIndex()).toBe(1);
    expect(component.currentQuestion()?.id).toBe('water-card-2');
    expect(component.progressPercent()).toBe(100);

    // Answer question 2
    component.selectOption('opt-w1');
    component.submitAnswer();
    component.nextQuestion();

    expect(component.isCompleted()).toBe(true);
  });

  it('should restart the challenge when requested', () => {
    component.currentIndex.set(1);
    component.isCompleted.set(true);

    component.restartChallenge();
    expect(component.currentIndex()).toBe(0);
    expect(component.isCompleted()).toBe(false);
  });
});
