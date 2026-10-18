# Oppia-Reference UI Reconstruction Map

**Date**: 2026-10-12  
**Target Application**: Digital Health Awareness (`health-awareness/frontend`)  
**Reference Codebase**: Oppia (`C:\Users\nalli\project-internship\oppia-reference`)  
**License**: Apache License 2.0 (Copyright 2014-2022 The Oppia Authors / The Oppia Foundation)

---

## 1. Executive Summary & Objective

This document serves as the authoritative, source-grounded specification for replacing the Health Awareness application's custom dark-mode interface with Oppia's real, learner-facing design patterns, styling tokens, component hierarchies, and interactive lesson player mechanics.

Rather than an arbitrary redesign or superficial mimicry, this reconstruction extracts concrete templates, CSS rules, layout constraints, and interaction conventions directly from the verified Oppia repository located at `C:\Users\nalli\project-internship\oppia-reference\`.

---

## 2. Core Oppia Design System Tokens & Global Tokens

Oppia's learner experience is characterized by clean white card surfaces, distinctive teal and deep-blue brand accents, sharp 2px/4px border radii, subtle Material-inspired box shadows, and readable Roboto/Capriola typography.

### 2.1 Design Token Comparison Matrix

| Token Category | Token Name | Oppia Reference Value | Current HealthAware Value | Target Replacement in HealthAware |
| :--- | :--- | :--- | :--- | :--- |
| **Canvas Background** | `--clr-bg-primary` | `#ffffff` / `#f5f5f5` | `hsl(228, 24%, 8%)` (Dark navy) | `#ffffff` |
| **Surface Background** | `--clr-bg-secondary` | `#f5f5f5` | `hsl(228, 20%, 12%)` | `#f8f9fa` |
| **Card Surface** | `--clr-bg-card` | `#ffffff` | `hsl(228, 18%, 14%)` | `#ffffff` |
| **Text Primary** | `--clr-text-primary` | `#212121` / `#333333` | `hsl(0, 0%, 95%)` | `#212121` |
| **Text Secondary** | `--clr-text-secondary` | `#616161` / `#6b7280` | `hsl(228, 12%, 68%)` | `#616161` |
| **Text Muted** | `--clr-text-muted` | `#9e9e9e` / `#9ca3af` | `hsl(228, 10%, 50%)` | `#757575` |
| **Primary Brand Teal** | `--clr-teal` | `#00645c` (`oppia.css:1046`) | None (custom purple/blue) | `#00645c` |
| **Deep Footer Teal** | `--clr-teal-dark` | `#094142` (`exploration-footer`) | None | `#094142` |
| **Primary Action Blue** | `--clr-blue` | `#0d48a1` (`continue-button`) | Gradient `linear-gradient(...)` | `#0d48a1` |
| **Action Blue Hover** | `--clr-blue-hover` | `#115fd4` (`multiple_choice_input`) | Glow hover effect | `#115fd4` |
| **Tutor Content Bubble** | `--clr-mint` | `rgba(224, 242, 241, 1)` (`#e0f2f1`) | Dark glass container | `rgba(224, 242, 241, 1)` |
| **Learner Answer Bubble**| `--clr-learner-bg`| `rgba(236, 239, 241, 1)` (`#eceff1`) | Dark glass container | `rgba(236, 239, 241, 1)` |
| **Borders** | `--clr-border` | `#d1d5db` / `#eee` | `hsl(228, 14%, 22%)` | `#d1d5db` |
| **Border Radii** | `--radius-sm`, `--radius-md` | `2px` / `4px` / `8px` | `1rem` / `1.5rem` (Bubble curves) | `2px` (buttons/bubbles), `8px` (cards) |
| **Heading Font** | `--ff-heading` | `'Capriola', 'Roboto', Arial, sans-serif` | `'Outfit', sans-serif` | `'Capriola', 'Roboto', Arial, sans-serif` |
| **Body Font** | `--ff-body` | `'Roboto', Arial, sans-serif` | `'Inter', sans-serif` | `'Roboto', Arial, sans-serif` |
| **Card Box Shadow** | `--shadow-card` | `0 0 8px 0 rgba(0, 0, 0, 0.2)` | `0 8px 32px rgba(...)` | `0 0 8px 0 rgba(0, 0, 0, 0.12)` |

### 2.2 Global File References
- **Oppia Core Styles**: `C:\Users\nalli\project-internship\oppia-reference\core\templates\css\oppia.css`
- **HealthAware Target Styles**: `C:\Users\nalli\project-internship\health-awareness\frontend\src\styles.css`

---

## 3. Experience 1: Homepage & Topic Discovery

### 3.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `core/templates/pages/classroom-page/classroom-page.component.html`
  - `core/templates/pages/classroom-page/classroom-page.component.css`
  - `core/templates/components/summary-tile/topic-summary-tile.component.html`
  - `core/templates/components/summary-tile/topic-summary-tile.component.css`
  - `core/templates/components/common-layout-directives/navigation-bars/top-navigation-bar.component.html`
  - `core/templates/components/common-layout-directives/navigation-bars/top-navigation-bar.component.css`
- **Key Oppia UI Characteristics**:
  - **Banner & Header**: Clean white container with `#00645c` banner or light title block, clear breadcrumbs (`Home > Health Topics`), bold h1 typography (`font-size: 2rem; font-weight: 500; font-family: Roboto`).
  - **Topic Summary Tile (`.topic-card`)**:
    - Outer card: `border-radius: 0.4em (4px - 6px)`, `box-shadow: 0 0 8px 0 rgba(0, 0, 0, 0.2)`, `background: #fff`.
    - Thumbnail area: Fixed height `120px` with theme-colored header stripe / icon representation.
    - Card details section (`.topic-details`): `padding: 12px`, `height: 100px`, `background-color: darker thumbnail color or clean white with dark text`, `font-family: Roboto`.
    - Topic title: `font-size: 1.25em`, `font-weight: 600`, clean high-contrast text.
    - Subtext / Lesson counter: `Total lessons available` with badge style.
  - **Grid Layout**: Responsive grid (`grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`, `gap: 24px`, `max-width: 1200px`, centered).

### 3.2 Target HealthAware Component Mapping
- **Component**: `frontend/src/app/pages/home/home.component.ts|html|css`
- **Backend API Integration**: `GET /api/v1/topics`
- **Data Contract Mapping**:
  - `topic.id` -> Navigation router link `/topics/:slug`
  - `topic.title` -> `.topic-name`
  - `topic.description` -> Course/topic summary text
  - `topic.lesson_count` -> Lesson badge (`X lessons`)
  - `topic.category` / `topic.slug` -> Topic accent banner color
- **Reuse vs. Adaptation**:
  - *Adapted Presentation*: The structural markup of `.topic-card` and `.topic-details` from `topic-summary-tile.component.html` is directly adapted into `HomeComponent`.
  - *Excluded Oppia Dependencies*: Oppia's `ClassroomData` domain service, `UrlInterpolationService`, and `I18nLanguageCodeService` are excluded in favor of standard Angular signals and `RouterLink`.

---

## 4. Experience 2: Topic & Lesson Listing

### 4.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `core/templates/pages/topic-viewer-page/topic-viewer-content/topic-viewer-content.component.html`
  - `core/templates/pages/topic-viewer-page/topic-story-section/topic-lesson-card/topic-lesson-card.component.html`
  - `core/templates/pages/topic-viewer-page/topic-story-section/topic-lesson-card/topic-lesson-card.component.css`
  - `core/templates/pages/topic-viewer-page/topic-story-section/module-circle-badge.component.html`
  - `core/templates/pages/topic-viewer-page/topic-story-section/module-circle-badge.component.css`
- **Key Oppia UI Characteristics**:
  - **Lesson Card Structure (`.topic-lesson-card`)**:
    - Container: `border: 1px solid #eee`, `border-radius: 8px`, `background: #fff`, `max-width: 912px`, `margin: 0 auto 16px`.
    - Left Thumbnail/Accent Bar: `width: 212px` (desktop), `background-color: #8ebbb6` or topic accent.
    - Content Container (`.topic-lesson-card-content`): `padding: 20px 22px 14px`, flex column with `gap: 12px`.
    - Circle Badge (`topic-module-circle-badge`): 36px circular badge with lesson number (1, 2, 3...) in `#00645c` or `#fff` with colored border.
    - Header & Title: `font-size: 24px`, `font-weight: 500`, `color: #3b3b3b`, `line-height: 24px`.
    - Description: `font-size: 17px`, `line-height: 24px`, `color: #3d3d3d`.
    - Action Buttons:
      - Primary Start Lesson Button (`.topic-lesson-card-start-button`): `background: #00645c`, `color: #fff`, `border-radius: 4px`, `height: 44px`, `font-size: 14px`, `font-weight: 700`, uppercase text.
      - Secondary Action (`.topic-lesson-card-secondary-button`): `border: 2px solid #00645c`, `color: #00645c`, `background: #edf7f5`, `border-radius: 4px`.
    - Completion Status: Completed badge with green checkmark icon (`#40a84f`).

### 4.2 Target HealthAware Component Mapping
- **Component**: `frontend/src/app/pages/topic-lessons/topic-lessons.component.ts|html|css`
- **Backend API Integration**: `GET /api/v1/topics/:topic_id/lessons`
- **Data Contract Mapping**:
  - `lesson.id` -> Router link `/lessons/:id`
  - `lesson.title` -> `.topic-lesson-card-title`
  - `lesson.summary` -> `.topic-lesson-card-description`
  - `lesson.order` / sequence index -> `.topic-module-circle-badge`
  - `lesson.status == 'published'` -> Start lesson active state
  - `lesson.sources` count -> Medical citations badge
- **Reuse vs. Adaptation**:
  - *Adapted Implementation*: Adapt the exact `.topic-lesson-card` layout and CSS variables from `topic-lesson-card.component.css`.
  - *Excluded Oppia Dependencies*: Oppia's story node graph, chapter prerequisites, and diagnostic test gating are replaced with direct lesson sequential progression.

---

## 5. Experience 3: Lesson Player (Tutor Card & Conversation Skin)

### 5.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/conversation-skin.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/conversation-skin.component.css`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/tutor-card.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/tutor-card.component.css`
  - `core/templates/pages/exploration-player-page/current-lesson-player/layout-directives/progress-nav.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/layout-directives/progress-nav.component.css`
- **Key Oppia UI Characteristics**:
  - **Outer Canvas (`.conversation-skin-cards-container`)**:
    - Max container width: `1400px`, centered.
    - Background: Light page background `#fff` or `#f8f9fa`.
  - **Tutor Card (`.oppia-learner-view-card`)**:
    - Container: `background: #fff`, `border-radius: 2px`, `box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)`, `max-width: 650px`, centered, `padding: 20px`.
  - **Tutor Content Bubble (`.oppia-learner-view-card-top-content`)**:
    - Background: `rgba(224, 242, 241, 1)` (Oppia mint-teal).
    - Border radius: `border-top-left-radius: 0` (speech bubble pointer effect).
    - Padding: `12px 16px`.
    - Text styling: `color: #212121`, `line-height: 1.6`, `font-size: 1rem`.
  - **Inline Interaction Section (`.conversation-skin-inline-interaction`)**:
    - Positioned directly inside or below the card top-content.
    - Padded `8px 20px 25px`.
  - **Progress & Navigation Bar (`.progress-nav-bar`)**:
    - White background, flex space-between.
    - Back button: Left aligned with `mat-raised-button` circular/flat arrow.
    - Primary Continue/Submit action: Right-aligned blue button `#0d48a1`.

### 5.2 Target HealthAware Component Mapping
- **Component**: `frontend/src/app/pages/lesson-player/lesson-player.component.ts|html|css`
- **Backend API Integration**: `GET /api/v1/lessons/:lesson_id`
- **Data Contract Mapping**:
  - `lesson.content_blocks` -> Paginated / stepped learner card content
  - `lesson.content_blocks[i].text` -> `.oppia-learner-view-card-top-content`
  - `lesson.content_blocks[i].media` -> Embedded media within tutor card
  - Step counter `i + 1 / total` -> Milestone progress bar
- **Reuse vs. Adaptation**:
  - *Adapted Presentation*: The exact conversation-skin container hierarchy (`.conversation-skin-tutor-card-container` -> `.oppia-learner-view-card` -> `.oppia-learner-view-card-top-content`) is preserved.
  - *Excluded Oppia Dependencies*: Oppia's `PlayerTranscriptService`, `AudioPlayerService`, and hybrid AngularJS expression engine are excluded. HealthAware's Angular signals drive card progression cleanly.

---

## 6. Experience 4: Interactive Single-Choice Question (MCQ)

### 6.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `extensions/interactions/MultipleChoiceInput/directives/multiple-choice-input-interaction.component.html`
  - `extensions/interactions/MultipleChoiceInput/static/multiple_choice_input.css`
  - `extensions/interactions/MultipleChoiceInput/directives/oppia-interactive-multiple-choice-input.component.ts`
- **Key Oppia UI Characteristics**:
  - **Option Container (`.multiple-choice-option-container`)**:
    - Padding: `4px 0`.
  - **Option Button (`.multiple-choice-option`)**:
    - `background: none`, `border: none`, `text-align: left`, `width: 100%`, `cursor: pointer`, `color: #0d48a1`.
    - Table-cell alignment layout (`.multiple-choice-radio-button-container` and `.multiple-choice-content-container` both `display: table-cell`).
  - **Custom Radio Button**:
    - Outer Ring (`.multiple-choice-outer-radio-button`):
      - Size: `16px x 16px`, circular (`border-radius: 50%`).
      - Border: `2px solid #0d48a1`.
      - Alignment: `display: flex; align-items: center; justify-content: center`.
    - Inner Dot (`.multiple-choice-inner-radio-button`):
      - When selected: `width: 8px; height: 8px; background-color: #115fd4; border-radius: 50%; display: block`.
  - **Hover & Focus Interactions**:
    - Desktop hover effect: `box-shadow: 0 0 0 8px rgba(80, 80, 200, 0.2); border-color: #115fd4`.
    - Focus visible: standard browser accessibility focus ring.

### 6.2 Target HealthAware Component Mapping
- **Component**: Embedded in `frontend/src/app/pages/lesson-player/lesson-player.component.html|css` (or dedicated interaction sub-component)
- **Data Contract Mapping**:
  - `lesson.questions` or active quiz block
  - `question.options` -> `choices` array (`choice.text`, `choice.index`)
  - Selection state signal `selectedOptionIndex` -> `.multiple-choice-option.selected`
- **Reuse vs. Adaptation**:
  - *Direct Markup & Style Adaptation*: Directly import the HTML hierarchy and CSS from `multiple_choice_input.css` verbatim into HealthAware.
  - *Excluded Oppia Dependencies*: Oppia's schema-driven HTML parsing (`oppia-rte-output-display`) and `CurrentInteractionService` event bus are replaced by Angular standard template binding `(click)="selectOption(idx)"`.

---

## 7. Experience 5: Answer Feedback & Continuation

### 7.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/input-response-pair.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/input-response-pair.component.css`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/continue-button.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/continue-button.component.css`
- **Key Oppia UI Characteristics**:
  - **Learner Answer Bubble (`.conversation-skin-learner-answer-content`)**:
    - Display: Right-aligned or learner message bubble.
    - Background: `rgba(236, 239, 241, 1)` (soft grey-blue).
    - Border radius: `border-bottom-right-radius: 0` (learner pointer).
    - Padding: `8px 12px`, `margin-bottom: 12px`.
  - **Tutor Feedback Bubble (`.conversation-skin-oppia-feedback-content`)**:
    - Display: Left-aligned tutor message bubble.
    - Background: `rgba(224, 242, 241, 1)` (mint-teal).
    - Border radius: `border-top-left-radius: 0` (tutor pointer).
    - Padding: `8px 12px`, `margin-bottom: 12px`.
  - **Feedback Tone**:
    - Correct: Positive reinforcement with explanation of medical evidence.
    - Incorrect: Constructive guidance with encouragement to review.
  - **Continue Button (`.oppia-learner-confirm-button`)**:
    - Background: `#0d48a1` (Oppia deep blue).
    - Hover background: `#115fd4`.
    - Border radius: `2px`.
    - Text: Uppercase `CONTINUE` with right arrow icon (`font-size: 19px; margin-left: 4px`).
    - Typography: `font-size: 16px; font-weight: 500; color: #fff`.

### 7.2 Target HealthAware Component Mapping
- **Component**: `frontend/src/app/pages/lesson-player/lesson-player.component.html|css`
- **Data Contract Mapping**:
  - `question.explanation` -> `.conversation-skin-oppia-feedback-content`
  - Selected choice label -> `.conversation-skin-learner-answer-content`
  - Continue action -> Triggers advance to next block or lesson completion
- **Reuse vs. Adaptation**:
  - *Direct Style Port*: Directly port the CSS rules from `input-response-pair.component.css` and `continue-button.component.css`.
  - *Excluded Oppia Dependencies*: Oppia feedback popovers and audio-sync markers are omitted.

---

## 8. Experience 6: Lesson Completion & Source Attribution

### 8.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `core/templates/pages/exploration-player-page/current-lesson-player/templates/lesson-information-card-modal.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/templates/lesson-information-card-modal.component.css`
  - `core/templates/pages/exploration-player-page/current-lesson-player/layout-directives/exploration-footer.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/layout-directives/exploration-footer.component.css`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/ratings-and-recommendations.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/learner-experience/ratings-and-recommendations.component.css`
- **Key Oppia UI Characteristics**:
  - **Completion State**:
    - Congratulatory milestone display with star badge and completed chapters count.
    - Completion summary card within `.oppia-learner-view-card`.
    - Action to return to topic page or advance to next topic lesson.
  - **Lesson Information & Source Card (`.oppia-lesson-info-card`)**:
    - Header banner with category badge and title.
    - Medical/Educational Sources and Contributors section (`.named-contributors-container` & `.oppia-info-card-bottom-row`).
    - Verification metadata: Last reviewed/updated date, review status badge.
    - Tags section with tag pill icons.
  - **Footer Bar (`.oppia-exploration-footer`)**:
    - Background: `#094142` (Dark Teal).
    - Height: `42px` fixed compact bar.
    - Font: `"Capriola", "Roboto", Arial, sans-serif`, `font-size: 13px`, `color: #fff`.
    - Lesson Info Trigger button with info icon (`fas fa-info-circle`) to open source modal/drawer.

### 8.2 Target HealthAware Component Mapping
- **Component**: `frontend/src/app/pages/lesson-player/lesson-player.component.html|css` & `frontend/src/app/components/footer/footer.component.html|css`
- **Backend API Integration**: `GET /api/v1/lessons/:lesson_id`
- **Health Content Preservation**:
  - Sources array: WHO, CDC, NHS citations, URLs, and retrieval dates.
  - Medical Review Status: `reviewed_by`, `review_date`, `status: "approved"`.
  - Clear health disclaimer preserved in source card.
- **Reuse vs. Adaptation**:
  - *Adapted Modal / Drawer*: Model the source attribution card directly after Oppia's `lesson-information-card-modal.component.html`.
  - *Adapted Footer*: Replace the bulky multi-column footer with Oppia's sleek `#094142` exploration footer.

---

## 9. Global Navigation: Top Navbar

### 9.1 Oppia Reference Patterns
- **Primary Source Files**:
  - `core/templates/components/common-layout-directives/navigation-bars/top-navigation-bar.component.html`
  - `core/templates/components/common-layout-directives/navigation-bars/top-navigation-bar.component.css`
  - `core/templates/pages/exploration-player-page/current-lesson-player/layout-directives/learner-view-info.component.html`
  - `core/templates/pages/exploration-player-page/current-lesson-player/layout-directives/learner-view-info.component.css`
  - `core/templates/css/oppia.css` (lines 1045-1048)
- **Key Oppia UI Characteristics**:
  - Background: Solid Oppia Teal `#00645c` (`height: 56px`, `width: 100%`).
  - Brand Logo & Title: White logo and text (`color: #fff`, `font-family: 'Capriola', 'Roboto', sans-serif`).
  - Breadcrumbs (`.oppia-navbar-breadcrumb`):
    - White text (`#fff`), font size `18px`.
    - Topic subtitle: `font-size: 12px`, opacity `0.85`.
  - Navigation Links: Clean white text with subtle underline hover (`border-bottom: 2px solid #fff`).

### 9.2 Target HealthAware Component Mapping
- **Component**: `frontend/src/app/components/navbar/navbar.component.ts|html|css`
- **Reuse vs. Adaptation**:
  - Adapt the solid `#00645c` teal navbar with white brand icon, breadcrumbs, and active navigation indicators.

---

## 10. Architectural Constraints & Dependency Separation

To guarantee clean, maintainable, and regression-free adaptation, the following boundaries are strictly enforced:

| Oppia Architecture Feature | Reason Direct Import is Infeasible | Selected HealthAware Adaptation |
| :--- | :--- | :--- |
| **AngularJS Hybrid Bridge** | Oppia still contains legacy AngularJS modules and hybrid upgrade adapters. HealthAware is a pure standalone Angular 19+ application. | Extract pure modern Angular template markup and CSS; avoid AngularJS dependencies. |
| **Oppia Python Backend (NDB/GAE)** | Oppia uses Python 3 GAE Datastore services with a completely different schema (Exploration models, State graphs). HealthAware uses its own Flask + Cloud NDB domain model. | Retain 100% of HealthAware's Flask REST API (`/api/v1/*`) and Python domain models. |
| **Oppia Translation Pipeline (`I18nLanguageCodeService`)** | Oppia uses custom multi-language schema translation and hacky translation keys. | Standard English health awareness strings directly embedded in templates with accessible aria attributes. |
| **Oppia Rich Text Format (`oppia-rte-output-display`)** | Oppia parses HTML RTE through custom DOM sanitizers and math equation widgets. | Angular's built-in `[innerHTML]` and sanitization pipelines for safe formatted lesson text. |
| **Oppia Audio / Voiceover Player** | Requires complex preloading and audio sprite manifests. Health awareness currently focuses on written content. | Audio player omitted from initial phase; layout space preserved. |

---

## 11. Licensing & Attribution Notice

In accordance with Section 8 of the project requirements and the Apache License, Version 2.0:
1. **Notice Preservation**: Any component markup, styles, or patterns directly adapted from Oppia retain copyright attribution:
   ```text
   Copyright 2014-2022 The Oppia Authors.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
   ```
2. **Attribution Documentation**: All adapted files record their origin path relative to `oppia-reference/`.

---

## 12. Component-by-Component Implementation Checklist

- [x] **Phase 1: Design System & Tokens**
  - Update `frontend/src/styles.css` with Oppia light tokens (`#00645c`, `#094142`, `#0d48a1`, `#e0f2f1`, `#eceff1`).
  - Configure Google Fonts for `Capriola` and `Roboto`.
- [x] **Phase 2: Global Navigation & Footer**
  - Overhaul `navbar.component.html|css` to Oppia `#00645c` solid teal bar.
  - Overhaul `footer.component.html|css` to Oppia `#094142` compact exploration footer.
- [x] **Phase 3: Home & Topic Discovery Page**
  - Overhaul `home.component.html|css` to Oppia classroom layout with `.topic-card` tiles.
  - Add For Community Educators section and Newsletter strip with functional Coming Soon toasts.
- [x] **Phase 4: Topic Lessons Listing**
  - Overhaul `topic-lessons.component.html|css` to Oppia `.topic-lesson-card` layout with chapter badge and duration tags.
- [x] **Phase 5: Lesson Player & Quiz Interaction**
  - Overhaul `lesson-player.component.html|css` to Oppia tutor card, mint feedback bubble, and `.multiple-choice-option` custom radio styling.
- [x] **Phase 6: Source Attribution Drawer & Completion**
  - Implement lesson info / source panel matching `lesson-information-card-modal.component.html`.
- [x] **Phase 7: Verification & Regression Testing**
  - Run `npm test` and `npm run build` in `frontend/` (33/33 tests passed, build successful).
  - Run `pytest` backend tests in `backend/` (107/107 tests passed: 68 unit + 39 integration).
  - Perform browser screenshot comparison across desktop and mobile.
