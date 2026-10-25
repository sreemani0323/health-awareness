import { Injectable, signal, computed, Optional } from '@angular/core';
import { LearnerAuthService } from './learner-auth.service';
import { NetworkStatusService } from './network-status.service';

export type ProgressSyncStatus =
  | 'local_only'
  | 'pending_sync'
  | 'syncing'
  | 'synced'
  | 'sync_error';

export interface LessonResumeState {
  lessonId: string;
  lessonTitle: string;
  topicId: string;
  cardIndex: number;
  totalCards: number;
  updatedAt: string;
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  icon: string;
  achievedAt: string;
}

export interface PracticalActivity {
  id: string;
  topicId: string;
  title: string;
  instruction: string;
  safetyNote: string;
  relatedLessonId: string;
  icon: string;
}

export interface StoredProgressData {
  version: number;
  lastLesson: LessonResumeState | null;
  completedLessonIds: string[];
  completedActivityIds: string[];
  achievedMilestones: Milestone[];
}

export const PRACTICAL_ACTIVITIES: PracticalActivity[] = [
  {
    id: 'act-handwashing-practice',
    topicId: 'topic-hygiene',
    title: '5-Step Handwashing Routine',
    instruction: 'Practice the full 20-second handwashing routine with soap and clean water together before your next meal.',
    safetyNote: 'Use clean running water (warm or cool) and regular soap; avoid scalding water which irritates skin.',
    relatedLessonId: 'lesson-handwashing',
    icon: '🧼',
  },
  {
    id: 'act-covered-water-check',
    topicId: 'topic-water',
    title: 'Covered Water Storage Inspection',
    instruction: 'Check that household drinking-water vessels are covered with tight lids and that cups or ladles are kept clean.',
    safetyNote: 'Never dip unwashed hands or cups directly into stored drinking water.',
    relatedLessonId: 'lesson-water-purification',
    icon: '🚰',
  },
  {
    id: 'act-dry-day-check',
    topicId: 'topic-mosquito',
    title: 'Weekly Mosquito "Dry-Day" Check',
    instruction: 'Inspect flowerpots, cooler trays, buckets, and coconut shells around your home. Tip and dry any standing water.',
    safetyNote: 'Only inspect safe, accessible areas around your home. Do not climb into unsafe locations.',
    relatedLessonId: 'lesson-mosquito-control',
    icon: '🦟',
  },
  {
    id: 'act-vaccine-schedule-check',
    topicId: 'topic-vaccine',
    title: 'Family Immunization Record Check',
    instruction: 'Locate your family vaccination or maternal-child health card and review upcoming routine vaccination dates.',
    safetyNote: 'Consult your local primary health center (PHC) or Anganwadi worker for official immunization schedules.',
    relatedLessonId: 'lesson-vaccine-basics',
    icon: '🛡️',
  },
];

const STORAGE_KEY = 'healthaware_progress_v1';

@Injectable({ providedIn: 'root' })
export class LearningProgressService {
  private readonly storageKey = STORAGE_KEY;
  private readonly pendingSyncKey = 'healthaware_progress_pending_sync_v1';

  readonly resumeState = signal<LessonResumeState | null>(null);
  readonly completedLessonIds = signal<string[]>([]);
  readonly completedActivityIds = signal<string[]>([]);
  readonly achievedMilestones = signal<Milestone[]>([]);
  readonly syncStatus = signal<ProgressSyncStatus>('local_only');
  readonly hasPendingSync = signal<boolean>(false);

  readonly hasResume = computed(() => this.resumeState() !== null);
  readonly completedCount = computed(() => this.completedLessonIds().length);
  readonly activitiesCount = computed(() => this.completedActivityIds().length);

  readonly syncStatusLabel = computed<string>(() => {
    switch (this.syncStatus()) {
      case 'synced':
        return 'Synced with account';
      case 'syncing':
        return 'Syncing with account…';
      case 'pending_sync':
        return 'Saved locally • Pending sync';
      case 'sync_error':
        return 'Saved locally • Sync issue';
      case 'local_only':
      default:
        return 'Saved on this device';
    }
  });

  private activeSyncPromise: Promise<void> | null = null;

  constructor(
    @Optional() private readonly learnerAuth?: LearnerAuthService,
    @Optional() private readonly networkStatus?: NetworkStatusService,
  ) {
    this.loadFromStorage();
    this.restorePendingSyncFlag();

    // Auto-sync listener when network transitions from offline to online
    if (this.networkStatus) {
      this.networkStatus.onReconnect(() => {
        if (this.learnerAuth?.isAuthenticated() && this.hasPendingSync()) {
          this.syncWithRemote().catch((e) =>
            console.warn('Auto-reconnect sync failed:', e)
          );
        }
      });
    }

    if (this.learnerAuth?.isAuthenticated()) {
      this.syncWithRemote().catch((e) => console.warn('Startup sync failed:', e));
    } else {
      this.syncStatus.set('local_only');
    }
  }

  /**
   * Record progressive step inside a lesson.
   * Does NOT mark the lesson as completed; only updates current card position.
   */
  saveLessonProgress(
    lessonId: string,
    lessonTitle: string,
    topicId: string,
    cardIndex: number,
    totalCards: number,
  ): void {
    if (!lessonId) return;

    const resume: LessonResumeState = {
      lessonId,
      lessonTitle: lessonTitle || 'Lesson',
      topicId: topicId || '',
      cardIndex: Math.max(0, cardIndex),
      totalCards: Math.max(1, totalCards),
      updatedAt: new Date().toISOString(),
    };

    this.resumeState.set(resume);
    this.persist();
  }

  /**
   * Mark a lesson as fully completed.
   * Triggered only when the learner explicitly reaches and clicks completion.
   */
  markLessonCompleted(lessonId: string, topicId: string): void {
    if (!lessonId) return;

    const currentCompleted = this.completedLessonIds();
    if (!currentCompleted.includes(lessonId)) {
      const updated = [...currentCompleted, lessonId];
      this.completedLessonIds.set(updated);
      this.checkAndAwardMilestones(lessonId, topicId, updated);
      this.persist();
    }
  }

  /**
   * Check whether a specific lesson has been completed on this device.
   */
  isLessonCompleted(lessonId: string): boolean {
    return this.completedLessonIds().includes(lessonId);
  }

  /**
   * Check whether a lesson is currently in-progress (started but not yet completed).
   */
  isLessonInProgress(lessonId: string): boolean {
    const resume = this.resumeState();
    return !this.isLessonCompleted(lessonId) && resume !== null && resume.lessonId === lessonId;
  }

  /**
   * Return the normalized progress status of a chapter.
   */
  getLessonStatus(lessonId: string): 'completed' | 'in_progress' | 'not_started' {
    if (this.isLessonCompleted(lessonId)) return 'completed';
    if (this.isLessonInProgress(lessonId)) return 'in_progress';
    return 'not_started';
  }

  /**
   * Reset progress and completion state for a single chapter.
   * Removes only the target lesson from completedLessonIds and clears resume state if it points to it.
   * Crucially preserves all other completed chapters, family activities, and achieved milestones.
   */
  resetLessonProgress(lessonId: string): void {
    if (!lessonId) return;

    const currentCompleted = this.completedLessonIds();
    const updated = currentCompleted.filter((id) => id !== lessonId);
    this.completedLessonIds.set(updated);

    const currentResume = this.resumeState();
    if (currentResume && currentResume.lessonId === lessonId) {
      this.resumeState.set(null);
    }

    this.clearMissedQuestions(lessonId);
    this.persist();
  }

  /**
   * Toggle completion of a practical family activity.
   */
  toggleActivity(activityId: string): boolean {
    const current = this.completedActivityIds();
    let updated: string[];
    let isNowCompleted = false;

    if (current.includes(activityId)) {
      updated = current.filter((id) => id !== activityId);
      isNowCompleted = false;
    } else {
      updated = [...current, activityId];
      isNowCompleted = true;
      this.checkActivityMilestone(updated);
    }

    this.completedActivityIds.set(updated);
    this.persist();
    return isNowCompleted;
  }

  /**
   * Check whether an activity is marked completed.
   */
  isActivityCompleted(activityId: string): boolean {
    return this.completedActivityIds().includes(activityId);
  }

  /**
   * Record completion of a topic mastery challenge and award milestone badge.
   */
  recordTopicMastery(topicId: string, score: number, total: number): void {
    if (total <= 0) return;
    const passed = (score / total) >= 0.7;
    if (!passed) return;

    const current = [...this.achievedMilestones()];
    const hasMilestone = (id: string) => current.some((m) => m.id === id);
    const now = new Date().toISOString();

    const topicMilestoneMap: Record<string, { id: string; title: string; desc: string; icon: string }> = {
      'topic-hygiene': {
        id: 'hygiene-topic-mastery',
        title: 'Personal Hygiene Scholar',
        desc: 'Mastered hygiene principles across personal, oral, and shared community environments.',
        icon: '🧼',
      },
      'topic-water': {
        id: 'water-topic-mastery',
        title: 'Safe Water Ambassador',
        desc: 'Mastered water safety, treatment, covered storage, and community vigilance.',
        icon: '🚰',
      },
      'topic-mosquito': {
        id: 'mosquito-topic-mastery',
        title: 'Vector Control Specialist',
        desc: 'Mastered breeding elimination, bite barriers, disease care, and community campaigns.',
        icon: '🦟',
      },
      'topic-vaccine': {
        id: 'vaccine-topic-mastery',
        title: 'Community Immunity Advocate',
        desc: 'Mastered vaccine mechanisms, schedules, reaction management, and respectful myth-busting.',
        icon: '🛡️',
      },
    };

    const target = topicMilestoneMap[topicId];
    if (target && !hasMilestone(target.id)) {
      current.push({
        id: target.id,
        title: target.title,
        description: target.desc,
        icon: target.icon,
        achievedAt: now,
      });
      this.achievedMilestones.set(current);
      this.persist();
    }
  }

  /**
   * Record a missed question for optional learner revision.
   */
  recordMissedQuestion(lessonId: string, questionPrompt: string): void {
    const key = `healthaware_revision_${lessonId}`;
    try {
      const existing = JSON.parse(localStorage.getItem(key) || '[]');
      if (!existing.includes(questionPrompt)) {
        existing.push(questionPrompt);
        localStorage.setItem(key, JSON.stringify(existing.slice(-20)));
      }
    } catch {
      // non-fatal localStorage error
    }
  }

  getMissedQuestions(lessonId: string): string[] {
    try {
      const key = `healthaware_revision_${lessonId}`;
      return JSON.parse(localStorage.getItem(key) || '[]');
    } catch {
      return [];
    }
  }

  clearMissedQuestions(lessonId: string): void {
    try {
      const key = `healthaware_revision_${lessonId}`;
      localStorage.removeItem(key);
    } catch {
      // non-fatal
    }
  }

  /**
   * Clear only the active lesson resume position / bookmark.
   * Preserves completed lesson IDs, family activity completions, and achieved milestones.
   */
  clearResumeProgress(): void {
    this.resumeState.set(null);
    this.persist();
  }

  /**
   * Clear all locally saved learning progress.
   * Crucial for privacy on shared family and community devices.
   */
  clearAllProgress(): void {
    try {
      localStorage.removeItem(this.storageKey);
    } catch (e) {
      console.warn('Unable to clear localStorage:', e);
    }
    this.resumeState.set(null);
    this.completedLessonIds.set([]);
    this.completedActivityIds.set([]);
    this.achievedMilestones.set([]);
  }

  /**
   * Get all defined practical activities.
   */
  getPracticalActivities(): PracticalActivity[] {
    return PRACTICAL_ACTIVITIES;
  }

  /**
   * Load stored state from localStorage safely.
   */
  private loadFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (!raw) return;

      const parsed: StoredProgressData = JSON.parse(raw);
      if (parsed && parsed.version === 1) {
        if (parsed.lastLesson && typeof parsed.lastLesson === 'object') {
          this.resumeState.set(parsed.lastLesson);
        }
        if (Array.isArray(parsed.completedLessonIds)) {
          this.completedLessonIds.set(parsed.completedLessonIds);
        }
        if (Array.isArray(parsed.completedActivityIds)) {
          this.completedActivityIds.set(parsed.completedActivityIds);
        }
        if (Array.isArray(parsed.achievedMilestones)) {
          this.achievedMilestones.set(parsed.achievedMilestones);
        }
      }
    } catch (e) {
      console.warn('Error reading learning progress from localStorage:', e);
    }
  }

  /**
   * Persist current state into localStorage safely.
   */
  private persist(): void {
    try {
      const payload: StoredProgressData = {
        version: 1,
        lastLesson: this.resumeState(),
        completedLessonIds: this.completedLessonIds(),
        completedActivityIds: this.completedActivityIds(),
        achievedMilestones: this.achievedMilestones(),
      };
      localStorage.setItem(this.storageKey, JSON.stringify(payload));
    } catch (e) {
      console.warn('Error saving learning progress to localStorage:', e);
    }

    if (!this.learnerAuth || !this.learnerAuth.isAuthenticated()) {
      this.syncStatus.set('local_only');
      return;
    }

    // Check connectivity before network sync
    if (this.networkStatus && !this.networkStatus.isOnline()) {
      this.syncStatus.set('pending_sync');
      this.savePendingSyncFlag(true);
      return;
    }

    this.syncStatus.set('syncing');
    this.learnerAuth
      .pushRemoteProgress({
        last_lesson: this.resumeState(),
        completed_lesson_ids: this.completedLessonIds(),
        completed_activity_ids: this.completedActivityIds(),
        achieved_milestones: this.achievedMilestones(),
        client_updated_at: new Date().toISOString(),
      })
      .then((res) => {
        if (res) {
          this.syncStatus.set('synced');
          this.savePendingSyncFlag(false);
        } else {
          this.syncStatus.set('pending_sync');
          this.savePendingSyncFlag(true);
        }
      })
      .catch((err) => {
        console.warn('Background progress sync failed:', err);
        this.syncStatus.set('pending_sync');
        this.savePendingSyncFlag(true);
      });
  }

  /**
   * Syncs device learning progress with the authenticated learner account.
   * Performs deterministic merge:
   * - completedLessonIds: set union
   * - completedActivityIds: set union
   * - achievedMilestones: union deduplicated by id (keeping earliest achievedAt)
   * - lastLesson: latest by updatedAt timestamp
   *
   * Protected by singleflight in-flight execution lock to avoid duplicate submissions.
   */
  async syncWithRemote(): Promise<void> {
    if (!this.learnerAuth || !this.learnerAuth.isAuthenticated()) {
      this.syncStatus.set('local_only');
      return;
    }

    // Avoid duplicate concurrent sync submissions
    if (this.activeSyncPromise) {
      return this.activeSyncPromise;
    }

    this.activeSyncPromise = this.performSyncWithRemote();
    try {
      await this.activeSyncPromise;
    } finally {
      this.activeSyncPromise = null;
    }
  }

  private async performSyncWithRemote(): Promise<void> {
    if (!this.learnerAuth || !this.learnerAuth.isAuthenticated()) {
      this.syncStatus.set('local_only');
      return;
    }

    if (this.networkStatus && !this.networkStatus.isOnline()) {
      this.syncStatus.set('pending_sync');
      this.savePendingSyncFlag(true);
      return;
    }

    this.syncStatus.set('syncing');

    try {
      const remote = await this.learnerAuth.fetchRemoteProgress();
      if (!remote) {
        this.syncStatus.set('pending_sync');
        this.savePendingSyncFlag(true);
        return;
      }

      // 1. Merge completed lesson IDs
      const mergedLessons = Array.from(
        new Set([...this.completedLessonIds(), ...(remote.completed_lesson_ids || [])])
      );

      // 2. Merge completed activity IDs
      const mergedActivities = Array.from(
        new Set([...this.completedActivityIds(), ...(remote.completed_activity_ids || [])])
      );

      // 3. Merge milestones (deduplicate by id, preserving earliest timestamp)
      const milestoneMap = new Map<string, Milestone>();
      for (const m of this.achievedMilestones()) {
        milestoneMap.set(m.id, m);
      }
      for (const rm of remote.achieved_milestones || []) {
        const existing = milestoneMap.get(rm.id);
        if (!existing) {
          milestoneMap.set(rm.id, {
            id: rm.id,
            title: rm.title,
            description: rm.description,
            icon: rm.icon,
            achievedAt: rm.achievedAt,
          });
        } else {
          if (rm.achievedAt && existing.achievedAt && rm.achievedAt < existing.achievedAt) {
            existing.achievedAt = rm.achievedAt;
          }
        }
      }
      const mergedMilestones = Array.from(milestoneMap.values());

      // 4. Merge last lesson resume state (choose newer updatedAt)
      const localResume = this.resumeState();
      const remoteResume = remote.last_lesson;
      let mergedResume: LessonResumeState | null = localResume;

      if (!localResume && remoteResume) {
        mergedResume = {
          lessonId: remoteResume.lessonId,
          lessonTitle: remoteResume.lessonTitle,
          topicId: remoteResume.topicId,
          cardIndex: remoteResume.cardIndex,
          totalCards: remoteResume.totalCards,
          updatedAt: remoteResume.updatedAt,
        };
      } else if (localResume && remoteResume) {
        if (
          remoteResume.updatedAt &&
          (!localResume.updatedAt || remoteResume.updatedAt > localResume.updatedAt)
        ) {
          mergedResume = {
            lessonId: remoteResume.lessonId,
            lessonTitle: remoteResume.lessonTitle,
            topicId: remoteResume.topicId,
            cardIndex: remoteResume.cardIndex,
            totalCards: remoteResume.totalCards,
            updatedAt: remoteResume.updatedAt,
          };
        }
      }

      // Update local signals
      this.completedLessonIds.set(mergedLessons);
      this.completedActivityIds.set(mergedActivities);
      this.achievedMilestones.set(mergedMilestones);
      this.resumeState.set(mergedResume);

      // Persist to local storage
      try {
        const payload: StoredProgressData = {
          version: 1,
          lastLesson: mergedResume,
          completedLessonIds: mergedLessons,
          completedActivityIds: mergedActivities,
          achievedMilestones: mergedMilestones,
        };
        localStorage.setItem(this.storageKey, JSON.stringify(payload));
      } catch (e) {
        console.warn('Error saving merged progress to localStorage:', e);
      }

      // Push merged state back to server
      const confirmed = await this.learnerAuth.pushRemoteProgress({
        last_lesson: mergedResume,
        completed_lesson_ids: mergedLessons,
        completed_activity_ids: mergedActivities,
        achieved_milestones: mergedMilestones,
        client_updated_at: new Date().toISOString(),
      });

      if (confirmed) {
        this.syncStatus.set('synced');
        this.savePendingSyncFlag(false);
      } else {
        this.syncStatus.set('pending_sync');
        this.savePendingSyncFlag(true);
      }
    } catch (err) {
      console.warn('Progress sync failed:', err);
      this.syncStatus.set('pending_sync');
      this.savePendingSyncFlag(true);
    }
  }

  private savePendingSyncFlag(pending: boolean): void {
    this.hasPendingSync.set(pending);
    try {
      if (pending) {
        localStorage.setItem(this.pendingSyncKey, 'true');
      } else {
        localStorage.removeItem(this.pendingSyncKey);
      }
    } catch {
      // ignore
    }
    this.networkStatus?.setPendingSyncCount(pending ? 1 : 0);
  }

  private restorePendingSyncFlag(): void {
    try {
      const isPending = localStorage.getItem(this.pendingSyncKey) === 'true';
      this.hasPendingSync.set(isPending);
      if (isPending) {
        this.syncStatus.set('pending_sync');
        this.networkStatus?.setPendingSyncCount(1);
      }
    } catch {
      // ignore
    }
  }

  /**
   * Evaluates friendly positive milestones without shame or pressure.
   */
  private checkAndAwardMilestones(
    lessonId: string,
    topicId: string,
    completedList: string[],
  ): void {
    const current = [...this.achievedMilestones()];
    const hasMilestone = (id: string) => current.some((m) => m.id === id);
    const now = new Date().toISOString();

    // 1. First lesson completed
    if (completedList.length >= 1 && !hasMilestone('first-lesson')) {
      current.push({
        id: 'first-lesson',
        title: 'First Step in Health Learning',
        description: 'Completed your first interactive lesson on HealthAware.',
        icon: '🌱',
        achievedAt: now,
      });
    }

    // 2. Handwashing lesson
    if (lessonId === 'lesson-handwashing' && !hasMilestone('hygiene-mastery')) {
      current.push({
        id: 'hygiene-mastery',
        title: 'Hand Hygiene Champion',
        description: 'Completed the 5-step, 20-second handwashing technique lesson.',
        icon: '🧼',
        achievedAt: now,
      });
    }

    // 3. Water purification lesson
    if (lessonId === 'lesson-water-purification' && !hasMilestone('safe-water-mastery')) {
      current.push({
        id: 'safe-water-mastery',
        title: 'Safe Water Guardian',
        description: 'Completed household water treatment and storage principles.',
        icon: '🚰',
        achievedAt: now,
      });
    }

    // 4. Mosquito prevention completed
    if (topicId === 'topic-mosquito' && !hasMilestone('mosquito-prevention')) {
      current.push({
        id: 'mosquito-prevention',
        title: 'Mosquito Defense Learner',
        description: 'Learned vector habitat reduction and household bite prevention.',
        icon: '🦟',
        achievedAt: now,
      });
    }

    // 5. Vaccines lesson
    if (lessonId === 'lesson-vaccine-basics' && !hasMilestone('vaccine-informed')) {
      current.push({
        id: 'vaccine-informed',
        title: 'Community Immunity Supporter',
        description: 'Learned how vaccines prime immune defenses and protect communities.',
        icon: '🛡️',
        achievedAt: now,
      });
    }

    this.achievedMilestones.set(current);
  }

  private checkActivityMilestone(activityList: string[]): void {
    const current = [...this.achievedMilestones()];
    const hasMilestone = (id: string) => current.some((m) => m.id === id);

    if (activityList.length >= 1 && !hasMilestone('first-activity')) {
      current.push({
        id: 'first-activity',
        title: 'Family Action Taken',
        description: 'Practiced a healthy family routine at home.',
        icon: '🏡',
        achievedAt: new Date().toISOString(),
      });
      this.achievedMilestones.set(current);
    }
  }
}
