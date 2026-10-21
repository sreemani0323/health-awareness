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
  block_type: 'text' | 'heading' | 'image_ref' | 'dialogue' | 'callout' | 'key_takeaway';
  body: string;
  speaker?: string;
  avatar?: string;
  side?: 'left' | 'right';
}

export interface CreatorInteraction {
  interaction_type: 'single_choice' | 'multi_select' | 'arrange_steps' | 'identify_risk' | 'myth_fact';
  question_prompt: string;
  incorrect_behaviour: 'retry' | 'continue';
  options: CreatorAnswerOption[];
  correct_order?: string[];
  hint?: string;
  scene_description?: string;
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

// --- Staff Applications & Vetting (Phase 1B) ---

export type StaffApplicationStatus =
  | 'pending_review'
  | 'under_review'
  | 'more_info_requested'
  | 'approved'
  | 'rejected'
  | 'withdrawn';

export interface VerificationChecklistData {
  contact_verified: boolean;
  affiliation_verified: boolean;
  role_criteria_met: boolean;
  verification_notes?: string;
}

export interface StaffApplicationHistoryItem {
  history_id: string;
  from_status: string;
  to_status: string;
  actor_id: string;
  actor_name: string;
  actor_role: string;
  action: string;
  decision_rationale?: string | null;
  metadata?: any;
  created_at?: string | null;
}

export interface StaffApplicationAdminItem {
  application_id: string;
  reference_id: string;
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string | null;
  requested_role: string;
  organization?: string | null;
  professional_title?: string | null;
  status: StaffApplicationStatus;
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  approved_role?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface StaffApplicationDetail extends StaffApplicationAdminItem {
  credential_reference?: string | null;
  portfolio_url?: string | null;
  statement_of_purpose: string;
  evidence_standards_acknowledged: boolean;
  child_safety_acknowledged: boolean;
  assigned_jurisdiction?: string | null;
  provisioned_user_id?: string | null;
  rejection_reason?: string | null;
  info_request_details?: string | null;
  applicant_notes?: string | null;
  internal_notes?: string | null;
  verification_checklist: VerificationChecklistData;
  history: StaffApplicationHistoryItem[];
}

export interface PublicStaffApplicationSubmitRequest {
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string;
  requested_role: string;
  organization?: string;
  professional_title?: string;
  credential_reference?: string;
  portfolio_url?: string;
  statement_of_purpose: string;
  evidence_standards_acknowledged: boolean;
  child_safety_acknowledged: boolean;
}

export interface PublicStaffApplicationView {
  reference_id: string;
  applicant_name: string;
  applicant_email: string;
  requested_role: string;
  status: StaffApplicationStatus;
  organization?: string | null;
  professional_title?: string | null;
  credential_reference?: string | null;
  portfolio_url?: string | null;
  statement_of_purpose: string;
  info_request_details?: string | null;
  applicant_notes?: string | null;
  rejection_reason?: string | null;
  approved_role?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

