/**
 * TypeScript interfaces for Creator Studio API responses.
 * These extend the public API models with creator-specific fields.
 */

// --- Creator Topic (includes status) ---

export interface CreatorTopic {
  id: string;
  title: string;
  slug: string;
  description: string;
  display_order: number;
  status: 'draft' | 'published' | 'archived';
  cover_image_ref: string | null;
  cover_image_alt: string | null;
}

// --- Creator Lesson (includes version pointers) ---

export interface CreatorLesson {
  id: string;
  topic_id: string;
  display_order: number;
  published_version_id: string | null;
  draft_version_id: string | null;
  title?: string;
  summary?: string;
  status?: 'draft' | 'submitted_for_review' | 'published' | 'archived';
  card_count?: number;
  version_number?: number;
  review_feedback?: string | null;
}

// --- Creator Version (includes status) ---

export interface CreatorVersion {
  id: string;
  lesson_id: string;
  version_number: number;
  title: string;
  summary: string;
  language: string;
  learning_objectives: string[];
  estimated_duration_minutes: number;
  status: 'draft' | 'submitted_for_review' | 'published' | 'archived';
  cards: CreatorCard[];
  source_ids: string[];
  sources?: CreatorSource[];
  author_id?: string | null;
  submitted_by?: string | null;
  review_feedback?: string | null;
}

export interface CreatorCard {
  id: string;
  position: number;
  card_type: 'explanation' | 'interaction' | 'recap';
  content_blocks: CreatorContentBlock[];
  source_ids: string[];
  interaction: CreatorInteraction | null;
}

export interface CreatorContentBlock {
  block_type: 'text' | 'heading' | 'image_ref';
  body: string;
}

export interface CreatorInteraction {
  interaction_type: 'single_choice';
  question_prompt: string;
  incorrect_behaviour: 'retry' | 'continue';
  options: CreatorAnswerOption[];
}

export interface CreatorAnswerOption {
  id: string;
  label: string;
  is_correct: boolean;
  feedback: string;
}

export interface CreatorSource {
  id: string;
  title: string;
  publisher: string;
  url: string;
  publication_date: string | null;
  access_date: string | null;
  jurisdiction: string | null;
}

// --- Auth ---

export interface AuthUser {
  user_id: string;
  username: string;
  display_name: string;
  role: 'contributor' | 'reviewer' | 'admin';
}

export interface LoginRequest {
  username: string;
  password: string;
}

// --- Administration ---

export interface AdminUser {
  user_id: string;
  username: string;
  display_name: string;
  role: 'contributor' | 'reviewer' | 'admin';
  is_active: boolean;
  created_at?: string | null;
}

export interface CreateUserRequest {
  username: string;
  display_name: string;
  role: 'contributor' | 'reviewer' | 'admin';
  password: string;
}

export interface AdminOverview {
  total_users: number;
  active_users: number;
  deactivated_users: number;
  users_by_role: {
    contributor: number;
    reviewer: number;
    admin: number;
  };
  total_topics: number;
  draft_topics: number;
  published_topics: number;
  pending_reviews: number;
}

