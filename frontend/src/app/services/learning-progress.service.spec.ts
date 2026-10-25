import { TestBed } from '@angular/core/testing';
import { LearningProgressService, PRACTICAL_ACTIVITIES } from './learning-progress.service';
import { LearnerAuthService } from './learner-auth.service';
import { NetworkStatusService } from './network-status.service';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('LearningProgressService', () => {
  let service: LearningProgressService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        LearningProgressService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(LearningProgressService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created with initial empty state and local_only sync status', () => {
    expect(service).toBeTruthy();
    expect(service.hasResume()).toBe(false);
    expect(service.resumeState()).toBeNull();
    expect(service.completedCount()).toBe(0);
    expect(service.activitiesCount()).toBe(0);
    expect(service.achievedMilestones().length).toBe(0);
    expect(service.syncStatus()).toBe('local_only');
    expect(service.syncStatusLabel()).toBe('Saved on this device');
    expect(service.hasPendingSync()).toBe(false);
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

  it('should reset only a single chapter progress and preserve other completed lessons and milestones', () => {
    // Setup 2 completed lessons and 1 milestone
    service.markLessonCompleted('lesson-handwashing', 'topic-hygiene');
    service.markLessonCompleted('lesson-water-purification', 'topic-water');
    service.saveLessonProgress('lesson-handwashing', 'Handwashing', 'topic-hygiene', 2, 4);

    expect(service.isLessonCompleted('lesson-handwashing')).toBe(true);
    expect(service.isLessonCompleted('lesson-water-purification')).toBe(true);
    expect(service.completedCount()).toBe(2);
    expect(service.achievedMilestones().length).toBeGreaterThan(0);
    const initialMilestonesCount = service.achievedMilestones().length;

    // Reset only lesson-handwashing
    service.resetLessonProgress('lesson-handwashing');

    expect(service.isLessonCompleted('lesson-handwashing')).toBe(false);
    expect(service.isLessonCompleted('lesson-water-purification')).toBe(true);
    expect(service.completedCount()).toBe(1);
    expect(service.resumeState()).toBeNull(); // Cleared because it was active on handwashing
    expect(service.achievedMilestones().length).toBe(initialMilestonesCount); // Milestones preserved!
  });

  it('should correctly distinguish not started, in progress, and completed states', () => {
    expect(service.getLessonStatus('lesson-sanitizer')).toBe('not_started');
    expect(service.isLessonInProgress('lesson-sanitizer')).toBe(false);

    // Start lesson
    service.saveLessonProgress('lesson-sanitizer', 'Sanitizer', 'topic-hygiene', 1, 3);
    expect(service.getLessonStatus('lesson-sanitizer')).toBe('in_progress');
    expect(service.isLessonInProgress('lesson-sanitizer')).toBe(true);

    // Complete lesson
    service.markLessonCompleted('lesson-sanitizer', 'topic-hygiene');
    expect(service.getLessonStatus('lesson-sanitizer')).toBe('completed');
    expect(service.isLessonInProgress('lesson-sanitizer')).toBe(false);
  });

  describe('Offline queueing and authenticated progress synchronization', () => {
    it('sets pending_sync and queues sync when authenticated learner is offline', () => {
      const mockAuth = {
        isAuthenticated: () => true,
        pushRemoteProgress: async () => null,
        fetchRemoteProgress: async () => null,
      } as unknown as LearnerAuthService;

      const mockNetwork = {
        isOnline: () => false,
        onReconnect: () => () => {},
        setPendingSyncCount: (c: number) => {},
      } as unknown as NetworkStatusService;

      const offlineService = new LearningProgressService(mockAuth, mockNetwork);
      offlineService.markLessonCompleted('lesson-handwashing', 'topic-hygiene');

      expect(offlineService.syncStatus()).toBe('pending_sync');
      expect(offlineService.syncStatusLabel()).toBe('Saved locally • Pending sync');
      expect(offlineService.hasPendingSync()).toBe(true);
      expect(offlineService.isLessonCompleted('lesson-handwashing')).toBe(true);
    });

    it('sets synced when authenticated learner pushes progress online successfully', async () => {
      let pushCalled = false;
      const mockAuth = {
        isAuthenticated: () => true,
        pushRemoteProgress: async (payload: any) => {
          pushCalled = true;
          return { version: 1, ...payload };
        },
        fetchRemoteProgress: async () => null,
      } as unknown as LearnerAuthService;

      const mockNetwork = {
        isOnline: () => true,
        onReconnect: () => () => {},
        setPendingSyncCount: () => {},
      } as unknown as NetworkStatusService;

      const onlineService = new LearningProgressService(mockAuth, mockNetwork);
      onlineService.markLessonCompleted('lesson-water-purification', 'topic-water');

      // Wait a tick for promise to resolve
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(pushCalled).toBe(true);
      expect(onlineService.syncStatus()).toBe('synced');
      expect(onlineService.syncStatusLabel()).toBe('Synced with account');
      expect(onlineService.hasPendingSync()).toBe(false);
    });

    it('merges remote progress deterministically using set-union and earliest milestone dates', async () => {
      const mockRemote = {
        version: 1,
        last_lesson: {
          lessonId: 'lesson-vaccine-basics',
          lessonTitle: 'Vaccine Basics',
          topicId: 'topic-vaccine',
          cardIndex: 2,
          totalCards: 4,
          updatedAt: '2026-10-24T10:00:00Z',
        },
        completed_lesson_ids: ['lesson-handwashing', 'lesson-water-purification'],
        completed_activity_ids: ['act-handwashing-practice'],
        achieved_milestones: [
          {
            id: 'first-lesson',
            title: 'First Step in Health Learning',
            description: 'Completed your first lesson.',
            icon: '🌱',
            achievedAt: '2026-10-20T10:00:00Z',
          },
        ],
      };

      let pushedPayload: any = null;
      const mockAuth = {
        isAuthenticated: () => true,
        fetchRemoteProgress: async () => mockRemote,
        pushRemoteProgress: async (payload: any) => {
          pushedPayload = payload;
          return { version: 1, ...payload };
        },
      } as unknown as LearnerAuthService;

      const mockNetwork = {
        isOnline: () => true,
        onReconnect: () => () => {},
        setPendingSyncCount: () => {},
      } as unknown as NetworkStatusService;

      const syncService = new LearningProgressService(mockAuth, mockNetwork);
      // Local has a different lesson completed
      syncService.markLessonCompleted('lesson-mosquito-control', 'topic-mosquito');

      await syncService.syncWithRemote();

      // Verified merge: set-union of local and remote completed lessons
      expect(syncService.isLessonCompleted('lesson-handwashing')).toBe(true);
      expect(syncService.isLessonCompleted('lesson-water-purification')).toBe(true);
      expect(syncService.isLessonCompleted('lesson-mosquito-control')).toBe(true);

      // Verified merge: activity preserved
      expect(syncService.isActivityCompleted('act-handwashing-practice')).toBe(true);

      // Verified merge: milestone preserved
      expect(syncService.achievedMilestones().some((m) => m.id === 'first-lesson')).toBe(true);

      // Verified merge pushed back to server
      expect(pushedPayload).toBeTruthy();
      expect(pushedPayload.completed_lesson_ids).toContain('lesson-mosquito-control');
      expect(pushedPayload.completed_lesson_ids).toContain('lesson-handwashing');
      expect(syncService.syncStatus()).toBe('synced');
    });

    it('singleflight prevents duplicate concurrent sync executions', async () => {
      let fetchCalls = 0;
      const mockAuth = {
        isAuthenticated: () => true,
        fetchRemoteProgress: async () => {
          fetchCalls++;
          await new Promise((resolve) => setTimeout(resolve, 50));
          return {
            version: 1,
            completed_lesson_ids: [],
            completed_activity_ids: [],
            achieved_milestones: [],
          };
        },
        pushRemoteProgress: async () => ({ version: 1 }),
      } as unknown as LearnerAuthService;

      const mockNetwork = {
        isOnline: () => true,
        onReconnect: () => () => {},
        setPendingSyncCount: () => {},
      } as unknown as NetworkStatusService;

      const syncService = new LearningProgressService(mockAuth, mockNetwork);

      // Call syncWithRemote twice concurrently
      const promise1 = syncService.syncWithRemote();
      const promise2 = syncService.syncWithRemote();

      await Promise.all([promise1, promise2]);

      // Singleflight must ensure only ONE remote fetch executed!
      expect(fetchCalls).toBe(1);
    });
  });
});
