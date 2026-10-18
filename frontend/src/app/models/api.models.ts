/**
 * TypeScript interfaces mirroring the backend REST API v1 response contract.
 *
 * These interfaces match the JSON shapes returned by:
 *   GET /api/v1/topics
 *   GET /api/v1/topics/:topic_id/lessons
 *   GET /api/v1/lessons/:lesson_id
 *   GET /api/v1/health
 */

// --- Envelope wrappers ---

export interface ApiResponse<T> {
  data: T;
  meta: ApiMeta;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

export interface ApiMeta {
  api_version: string;
}

// --- Topic ---

export interface Topic {
  id: string;
  title: string;
  slug: string;
  description: string;
  display_order: number;
  cover_image_ref: string | null;
  cover_image_alt: string | null;
}

// --- Lesson Summary (for topic lessons listing) ---

export interface LessonSummary {
  id: string;
  topic_id: string;
  title: string;
  summary: string;
  language: string;
  estimated_duration_minutes: number;
  published_version_id: string;
  display_order: number;
}

// --- Lesson Detail ---

export interface ContentBlock {
  block_type: 'text' | 'heading' | 'image_ref';
  body: string;
}

export interface AnswerOption {
  id: string;
  label: string;
  is_correct: boolean;
  feedback: string;
}

export interface Interaction {
  interaction_type: 'single_choice';
  question_prompt: string;
  incorrect_behaviour: 'retry' | 'continue';
  options: AnswerOption[];
}

export interface LessonCard {
  id: string;
  position: number;
  card_type: 'explanation' | 'interaction' | 'recap';
  content_blocks: ContentBlock[];
  source_ids: string[];
  interaction: Interaction | null;
}

export interface HealthSource {
  id: string;
  title: string;
  publisher: string;
  url: string;
  publication_date: string | null;
  access_date: string | null;
  jurisdiction: string | null;
}

export interface LessonDetail {
  id: string;
  topic_id: string;
  version_id: string;
  version_number: number;
  title: string;
  summary: string;
  language: string;
  learning_objectives: string[];
  estimated_duration_minutes: number;
  cards: LessonCard[];
  sources: HealthSource[];
}

// --- Health check ---

export interface HealthCheck {
  status: string;
}
