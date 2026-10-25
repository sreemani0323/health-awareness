# ADR 0001: Native Android Footer Suppression

## Context & Problem Statement
The HealthAware web application features an extensive Oppia-faithful footer containing mission statements, multiple link columns, community forum links, blog links, and social channel buttons.
During testing on physical Android devices, the user identified that this lengthy footer creates severe clutter and poor ergonomics inside the native mobile app, where screen space is constrained and a native bottom navigation bar (`ha-bottom-nav`) is already provided.
However, desktop browsers and mobile web visitors still require the footer for navigation, SEO, and institutional links.

## Decision Drivers
- Ergonomics: Mobile application users expect modern app navigation (bottom tabs) rather than a desktop website footer.
- Maintainability: Maintain a single shared Angular codebase across web and native Capacitor APK.
- Correctness: Do not rely solely on viewport width media queries (since mobile web visitors on phones still expect normal web footer navigation).
- Accessibility: Ensure primary routes (Home, Learn, Report, Track) remain directly accessible via `ha-bottom-nav`.

## Considered Options
1. Viewport width CSS media query (`@media (max-width: 768px)` hide footer).
   - Rejected: This hides the footer on mobile browsers as well, breaking the web experience.
2. Capacitor native runtime detection (`Capacitor.isNativePlatform()`).
   - Selected: Supported, reliable, and decoupled from viewport dimensions.

## Decision Outcome
Inject `ApiConfigService` (which provides `isNative` via `Capacitor.isNativePlatform()`) into `FooterComponent`.
Inside `footer.component.html`, wrap the footer content with `@if (!isNative)`.
On native Android Capacitor builds, the footer is omitted from the DOM, and content maintains appropriate bottom padding (`env(safe-area-inset-bottom) + 64px`) to prevent overlap with `ha-bottom-nav`.
On web browsers (desktop and mobile web), the full footer continues to render as before.
