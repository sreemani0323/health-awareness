import { TestBed } from '@angular/core/testing';
import { LearningProgressService, PRACTICAL_ACTIVITIES } from './learning-progress.service';

describe('LearningProgressService', () => {
  let service: LearningProgressService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(LearningProgressService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created with initial empty state', () => {
    expect(service).toBeTruthy();
    expect(service.hasResume()).toBe(false);
    expect(service.resumeState()).toBeNull();
    expect(service.completedCount()).toBe(0);
    expect(service.activitiesCount()).toBe(0);
    expect(service.achievedMilestones().length).toBe(0);
  });

  it('should save and update resume position without marking lesson completed', () => {
    service.saveLessonProgress(
      'lesson-handwashing',
      'Effective Handwashing Techniques',
      'topic-hygiene',
      1,
      3
    );

    expect(service.hasResume()).toBe(true);
    const resume = service.resumeState();
    expect(resume?.lessonId).toBe('lesson-handwashing');
    expect(resume?.cardIndex).toBe(1);
    expect(resume?.totalCards).toBe(3);
    expect(service.isLessonCompleted('lesson-handwashing')).toBe(false);
  });

  it('should mark lesson as completed and award positive milestones', () => {
    service.markLessonCompleted('lesson-handwashing', 'topic-hygiene');

    expect(service.isLessonCompleted('lesson-handwashing')).toBe(true);
    expect(service.completedCount()).toBe(1);

    const milestones = service.achievedMilestones();
    expect(milestones.some((m) => m.id === 'first-lesson')).toBe(true);
    expect(milestones.some((m) => m.id === 'hygiene-mastery')).toBe(true);
  });

  it('should toggle practical family activities', () => {
    const actId = PRACTICAL_ACTIVITIES[0].id;
    expect(service.isActivityCompleted(actId)).toBe(false);

    const nowActive = service.toggleActivity(actId);
    expect(nowActive).toBe(true);
    expect(service.isActivityCompleted(actId)).toBe(true);
    expect(service.activitiesCount()).toBe(1);
    expect(service.achievedMilestones().some((m) => m.id === 'first-activity')).toBe(true);

    const toggledOff = service.toggleActivity(actId);
    expect(toggledOff).toBe(false);
    expect(service.isActivityCompleted(actId)).toBe(false);
    expect(service.activitiesCount()).toBe(0);
  });

  it('should safely clear all progress for shared-device privacy', () => {
    service.saveLessonProgress('lesson-water-purification', 'Safe Water', 'topic-water', 2, 5);
    service.markLessonCompleted('lesson-water-purification', 'topic-water');
    service.toggleActivity(PRACTICAL_ACTIVITIES[1].id);

    expect(service.hasResume()).toBe(true);
    expect(service.completedCount()).toBe(1);

    service.clearAllProgress();

    expect(service.hasResume()).toBe(false);
    expect(service.resumeState()).toBeNull();
    expect(service.completedCount()).toBe(0);
    expect(service.activitiesCount()).toBe(0);
    expect(service.achievedMilestones().length).toBe(0);
    expect(localStorage.getItem('healthaware_progress_v1')).toBeNull();
  });

  it('should restore state from localStorage upon initialization', () => {
    service.saveLessonProgress('lesson-vaccine-basics', 'Vaccines', 'topic-vaccine', 0, 3);
    service.markLessonCompleted('lesson-vaccine-basics', 'topic-vaccine');

    // Simulate new service instance
    const freshService = new LearningProgressService();
    expect(freshService.hasResume()).toBe(true);
    expect(freshService.resumeState()?.lessonId).toBe('lesson-vaccine-basics');
    expect(freshService.isLessonCompleted('lesson-vaccine-basics')).toBe(true);
  });
});
