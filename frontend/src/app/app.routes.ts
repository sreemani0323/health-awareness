import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { TopicsComponent } from './pages/topics/topics.component';
import { TopicLessonsComponent } from './pages/topic-lessons/topic-lessons.component';
import { LessonPlayerComponent } from './pages/lesson-player/lesson-player.component';
import { FamilyChallengeComponent } from './pages/challenge/family-challenge.component';
import { Login } from './pages/creator/login/login';
import { Dashboard } from './pages/creator/dashboard/dashboard';
import { TopicEditor } from './pages/creator/topic-editor/topic-editor';
import { LessonEditor } from './pages/creator/lesson-editor/lesson-editor';
import { PreviewComponent } from './pages/creator/preview/preview';
import { ReviewQueue } from './pages/creator/review-queue/review-queue';
import { AdminWorkspaceComponent } from './pages/creator/admin/admin';
import { ReportConcernComponent } from './pages/report/report.component';
import { TrackConcernComponent } from './pages/track/track.component';
import { StaffDashboardComponent } from './pages/staff/staff.component';
import { StaffApplyComponent } from './pages/staff/apply/staff-apply.component';
import { StaffStatusComponent } from './pages/staff/status/staff-status.component';

export const routes: Routes = [
  {
    path: '',
    component: HomeComponent,
    pathMatch: 'full',
    title: 'HealthAware — Evidence-Based Health Education',
  },
  {
    path: 'topics',
    component: TopicsComponent,
    title: 'Health Topics — HealthAware',
  },
  {
    path: 'learn',
    redirectTo: 'topics',
    pathMatch: 'full',
  },
  {
    path: 'topics/:topicId',
    component: TopicLessonsComponent,
    title: 'Topic Lessons — HealthAware',
  },
  {
    path: 'lessons/:lessonId',
    component: LessonPlayerComponent,
    title: 'Interactive Lesson — HealthAware',
  },
  {
    path: 'challenge',
    component: FamilyChallengeComponent,
    title: 'Family Learning Challenge — HealthAware',
  },
  // --- Citizen Report a Concern & Tracking Routes ---
  {
    path: 'report',
    component: ReportConcernComponent,
    title: 'Report a Concern — HealthAware Community Intake',
  },
  {
    path: 'track',
    component: TrackConcernComponent,
    title: 'Track Your Concern — HealthAware',
  },
  {
    path: 'staff',
    component: StaffDashboardComponent,
    title: 'Staff Case Management — HealthAware',
  },
  // --- Public Staff Application & Vetting Routes (Phase 1B) ---
  {
    path: 'staff/apply',
    component: StaffApplyComponent,
    title: 'Apply for Staff & Reviewer Roles — HealthAware',
  },
  {
    path: 'staff/application-status',
    component: StaffStatusComponent,
    title: 'Track Staff Application — HealthAware',
  },
  // --- Creator Studio Routes ---
  {
    path: 'creator/login',
    component: Login,
    title: 'Creator Studio Sign In — HealthAware',
  },
  {
    path: 'creator',
    component: Dashboard,
    title: 'Creator Studio Dashboard — HealthAware',
  },
  {
    path: 'creator/topic/new',
    component: TopicEditor,
    title: 'Create Topic — HealthAware Studio',
  },
  {
    path: 'creator/topics/new',
    component: TopicEditor,
    title: 'Create Topic — HealthAware Studio',
  },
  {
    path: 'creator/topic/:topicId',
    component: TopicEditor,
    title: 'Edit Topic — HealthAware Studio',
  },
  {
    path: 'creator/topics/:topicId',
    component: TopicEditor,
    title: 'Edit Topic — HealthAware Studio',
  },
  {
    path: 'creator/lesson/:lessonId',
    component: LessonEditor,
    title: 'Lesson Editor — HealthAware Studio',
  },
  {
    path: 'creator/lessons/:lessonId',
    component: LessonEditor,
    title: 'Lesson Editor — HealthAware Studio',
  },
  {
    path: 'creator/preview/:versionId',
    component: PreviewComponent,
    title: 'Draft Preview — HealthAware Studio',
  },
  {
    path: 'creator/reviews',
    component: ReviewQueue,
    title: 'Review Queue — HealthAware Studio',
  },
  {
    path: 'creator/admin',
    component: AdminWorkspaceComponent,
    title: 'Administration Workspace — HealthAware Studio',
  },
  {
    path: '**',
    redirectTo: '',
  },
];
