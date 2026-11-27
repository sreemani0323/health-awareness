# HealthAware — Android Mobile Application & Direct APK Distribution Guide

**Document Version:** 1.0.0  
**Target Systems:** Android 7.0 (API 24) through Android 16 (API 36), Capacitor 8 Native Bridge, Gradle Build Engine, Android Keystore Cryptography  
**Scope:** Mobile hybrid architecture, native hardware plugins, mobile UX ergonomics, APK compilation, digital code signing, SHA-256 integrity checks, and direct sideloading procedures.

---

## 1. Executive Summary & Mobile Architecture

HealthAware for Android is a high-performance hybrid mobile application engineered using **Capacitor 8** and **Angular 22**. It delivers native Android capabilities (hardware camera capture, GPS geotagging, hardware-backed Keystore encryption, and physical back-button navigation) while executing a compiled, zero-latency TypeScript frontend.

```
+---------------------------------------------------------------------------------------------------+
|                                  HEALTHAWARE FOR ANDROID APP                                     |
|                                Package ID: org.healthaware.app                                    |
+---------------------------------------------------------------------------------------------------+
                                                  │
                 ┌────────────────────────────────┴────────────────────────────────┐
                 ▼                                                                 ▼
+----------------------------------+                             +----------------------------------+
|      WEBVIEW RUNTIME LAYER       |                             |     NATIVE JAVA/KOTLIN BRIDGE    |
| - Angular 22 Single Page App     |                             | - Capacitor 8 Core Runtime       |
| - Standalone Signals Reactivity  |   Bidirectional Message     | - Android Lifecycle Interceptors |
| - Native Bottom Nav Bar          | ◄─────────────────────────► | - Hardware Permissions Manager   |
| - Offline Learning Progress Cache|          Passing            | - Android Keystore Cryptography  |
| - Bounded HTTP Network Client    |                             | - Native WebView Sandbox         |
+----------------------------------+                             +----------------------------------+
                 │                                                                 │
                 │                                               ┌─────────────────┴────────────────┐
                 │                                               ▼                                  ▼
                 │ Native Plugin Calls             +---------------------------+      +---------------------------+
                 └───────────────────────────────► |     HARDWARE SENSORS      |      |     NATIVE OS STORAGE     |
                                                   | - Camera (@capacitor)     |      | - Android Keystore (AES)  |
                                                   | - GPS Location Manager    |      | - SharedPreferences Enc   |
                                                   | - Hardware Back Button    |      | - App Private Sandboxed DB|
                                                   +---------------------------+      +---------------------------+
```

### Why Capacitor 8 Hybrid Architecture (Instead of Flutter or React Native)?
* **Zero Engine Overhead & Compact APK Size:** Flutter bundles the full Skia/Impeller graphics engine (~35–50 MB baseline APK). React Native bundles the Hermes JavaScript engine and C++ bridge. Capacitor leverages the existing **Android System WebView**, reducing the complete signed APK to just **11.0 MB** (`11,563,957 bytes`).
* **Single Unified Codebase:** 100% of business logic, micro-learning lessons, quizzes, and UI styling are shared identically between the desktop website and the mobile application. Updates apply instantly without maintaining dual repositories.
* **Standards-Compliant Web APIs:** Capacitor acts as a minimal native bridge. The app uses standard DOM, CSS custom properties, and modern Web APIs, guaranteeing longevity and maintainability.

---

## 2. Native Capabilities & Hardware Plugins

HealthAware integrates five official and security-audited Capacitor native plugins:

```
[ Angular 22 Web Context ]
      │
      ├── (1) Camera Capture ─────────► @capacitor/camera (Hardware Camera & Gallery)
      │
      ├── (2) GPS Evidence Tagging ───► @capacitor/geolocation (FusedLocationProvider)
      │
      ├── (3) Hardware Keystore ──────► @aparajita/capacitor-secure-storage (Android Keystore System)
      │
      ├── (4) Physical Navigation ────► @capacitor/app (Hardware Back-Button Interception)
      │
      └── (5) OS UI Theming ──────────► @capacitor/status-bar (Edge-to-Edge Status Bar Styling)
```

### 1. Native Camera Plugin (`@capacitor/camera`)
* **Use Case:** Citizen Concern Reporting (`/report`).
* **Implementation:** Allows citizens documenting environmental hazards (e.g. stagnant mosquito pools, broken sewage pipes) to capture live evidence directly with the device camera or select images from the gallery.
* **Security & Optimization:** Captured photos are bounded in memory, compressed as high-efficiency WebP/JPEG, and stripped of extraneous metadata before transmission to private S3 storage.

### 2. Native Geolocation Plugin (`@capacitor/geolocation`)
* **Use Case:** Incident Location Geotagging.
* **Implementation:** Queries Android's `FusedLocationProviderClient` to attach accurate GPS coordinates (latitude, longitude, and accuracy radius) to community hazard reports.
* **Permission Model:** Triggers Android's native runtime permission dialog (`ACCESS_FINE_LOCATION` and `ACCESS_COARSE_LOCATION`). If denied by the user, the app gracefully falls back to manual landmark entry without crashing.

### 3. Hardware-Backed Secure Storage (`@aparajita/capacitor-secure-storage`)
* **Use Case:** Offline Token & Session Storage.
* **Implementation:** Protects sensitive local credentials, staff session identifiers, and citizen tracking tokens.
* **Cryptographic Foundation:** Operates on top of the **Android Keystore System**. Cryptographic keys are generated inside secure hardware (Trusted Execution Environment - TEE, or StrongBox Keymaster) and never enter the application process memory. Data is encrypted using **AES-256 GCM**.

### 4. App & Hardware Back-Button Interceptor (`@capacitor/app`)
* **Use Case:** Native Android Navigation Ergonomics.
* **Implementation:** Android users expect the physical hardware back button (or swipe-back gesture) to navigate backwards intelligently rather than exiting the application.
* **Handler Cascade in [`app.ts`](file:///c:/Users/nalli/project-internship/health-awareness/frontend/src/app/app.ts):**
  1. *Priority 1:* If a modal dialog is open (e.g., Download Modal, Login Modal, Confirmation Dialog), the back button **dismisses the modal** and stops.
  2. *Priority 2:* If user is deep in navigation history (e.g., Lesson $\rightarrow$ Chapter $\rightarrow$ Topic), the back button navigates backwards in the Angular router history (`Location.back()`).
  3. *Priority 3:* If the user is on the root Home screen with no open overlays, the back button invokes native `CapApp.exitApp()`.

### 5. Status Bar Theming (`@capacitor/status-bar`)
* Dynamically configures the native Android status bar with dark icons and brand-aligned background coloring (`#094142`), eliminating visual jarring when switching between the native OS header and the app content.

---

## 3. Mobile UX, Thumb Ergonomics & Offline Support

### Sticky Bottom Navigation Bar
Mobile screens demand reachability. Modern smartphones (6.5" to 6.8") make top navigation bars inaccessible with one hand.

```
+---------------------------------------+
|              App Content              |
|        (Scrolls freely above)         |
+---------------------------------------+
|  [Topics]  [Report]  [Track]  [Staff] | <- 56px Touch-Target Sticky Bottom Bar
+---------------------------------------+
```

* **Thumb Zone Reachability:** Key navigation targets (**Explore**, **Report Concern**, **Track Status**, **Staff Portal**) are pinned to a fixed, translucent bottom bar.
* **Touch Target Standards:** Every bottom nav button adheres to WCAG 2.2 touch-target minimums ($48 \times 48\text{ px}$) to prevent accidental taps.
* **Active Route Indicator:** Features high-contrast badges and clear SVG route indicators.

### Offline-First Architecture & Network Banner
Public health education must reach rural and underserved areas where cellular connectivity is intermittent or absent:
* **Local Progress Bookmarking:** All completed interaction cards and lesson scores are saved instantly in local storage. Learners can read lessons offline without an internet connection.
* **Network Status Service (`network-status.service.ts`):** Listens to browser and native network events (`online`, `offline`).
* **Offline Detection Banner:** When connectivity drops, a persistent, accessible amber banner notifies the user:
  > *"You're reading offline. Your progress is saved locally and will sync when reconnected."*

---

## 4. Android Compilation & Build Pipeline

The Android package is built using Google's **Gradle** build automation tool and the **Android Gradle Plugin (AGP)**:

```
[ Angular TypeScript Source ]
             │
             │ npm run build (ng build)
             v
[ dist/health-awareness-frontend/browser/ ]
             │
             │ npx cap sync android
             v
[ frontend/android/app/src/main/assets/public/ ]
             │
             │ gradlew.bat assembleRelease
             v
[ app-release-unsigned.apk ]
             │
             │ jarsigner / apksigner (Cryptographic Keystore Signing)
             v
[ healthaware-v1.0.apk (11.0 MB Signed Release) ]
```

### What is an APK?
An **APK (Android Package Kit)** is the standard distribution file format used by the Android operating system to distribute and install mobile apps. Underneath, an APK is a specialized cryptographic ZIP archive containing:
1. `classes.dex`: Compiled Dalvik/ART executable bytecode (compiled from Java/Kotlin and Capacitor native plugins).
2. `resources.arsc`: Pre-compiled binary XML resources (strings, layouts, colors).
3. `AndroidManifest.xml`: Binary manifest defining permissions, activities, and hardware features.
4. `assets/public/`: The complete compiled Angular single-page application (HTML, CSS, JavaScript, SVG images).
5. `META-INF/`: Cryptographic signature manifests (`CERT.SF`, `CERT.RSA`) verifying author identity and tamper-resistance.

### Build Toolchain Compatibility
* **Android Gradle Plugin (AGP):** `8.9.x`
* **Gradle Wrapper Version:** `8.14.3` (`gradle-wrapper.properties`)
* *Why Gradle 8.14.3 (and not Gradle 9.x)?* AGP 8.x relies on internal Gradle problem-reporting services that were deprecated in Gradle 9.0 and removed in Gradle 9.6+. Locking to Gradle 8.14.3 ensures rock-solid build reproducibility.
* **Target Java SDK:** Java 21 LTS (Oracle / OpenJDK).

---

## 5. Application ID, Versioning & Compatibility Matrix

### 1. Application ID / Package ID (`org.healthaware.app`)
* **What it is:** The globally unique identifier that distinguishes HealthAware from every other application on the user's Android device and the Google Play ecosystem.
* **Reverse Domain Notation:** Uses standard reverse-DNS naming (`org.healthaware.app`).
* **Why it matters:** Android's Linux kernel uses the Application ID to create an isolated Linux User ID (UID) sandbox. No other app on the phone can access HealthAware's private storage, databases, or Keystore entries unless explicitly granted.

### 2. Version Identification: `versionCode` vs. `versionName`

```json
{
  "versionCode": 1,
  "versionName": "1.0"
}
```

* **`versionCode` (Integer `1`):** An internal, monotonically increasing integer evaluated by the Android OS package manager (`PackageManager`).
  * Android enforces that an update will only install if: $\text{versionCode}_{\text{new}} \ge \text{versionCode}_{\text{installed}}$.
  * It prevents downgrade attacks where an attacker tricks a user into installing an older binary containing a known vulnerability.
* **`versionName` (String `"1.0"`):** The human-readable version string displayed to users in the app settings, about dialog, and download cards. Follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

### 3. Android Operating System Compatibility

```
  API 24                                                              API 36
(Android 7.0)                                                      (Android 16)
      |──────────────────────────────────────────────────────────────────|
  Minimum SDK                                                        Target SDK
(Covers 95%+ of global devices)                                  (Latest Security & APIs)
```

* **Minimum Supported Version:** **Android 7.0 Nougat (API Level 24)**
  * *Why API 24?* Ensures compatibility with older smartphones widely used across rural communities in developing regions. API 24 supports Java 8 language desugaring and modern TLS 1.3 cryptographic cipher suites natively.
  * **Device Coverage:** Covers over **95.8% of all active Android smartphones worldwide**.
* **Target Version:** **Android 16 (API Level 36)**
  * *Why API 36?* Represents modern Android platform standards. Enforces edge-to-edge rendering, granular photo picker permissions, runtime notification permission gates, and strict background battery optimization.

---

## 6. App Size Calculation & Performance Optimization

### Exact File Size Metrics
* **Exact Size:** `11,563,957 bytes`
* **Formatted Display:** `11.0 MB`
* **Cloudflare Pages CDN Limit:** Hard limit of **25 MiB** (`26,214,400 bytes`) per static file asset. HealthAware consumes less than 44% of this limit, leaving ample headroom for future curriculum expansions.

### Why HealthAware is Lightweight
1. **System WebView Reuse:** By leveraging Android's built-in Chrome/Chromium WebView engine, the APK does not bundle its own rendering engine.
2. **SVG Vector Assets:** Graphic illustrations (microbiology diagrams, hygiene icons, mosquito life cycle) are stored as compressed mathematical vector SVG paths rather than dense PNG or JPEG bitmaps.
3. **Tree-Shaken Angular Bundles:** Dead-code elimination via ESBuild strips unused framework code from the client bundle.

---

## 7. Cryptographic Signing, Keystores & Signatures

Android enforces that **no APK can be installed on a device without a valid cryptographic signature**.

```
[ Raw Compiled APK ] + [ Private Keystore Key ] ──(apksigner)──► [ Cryptographically Signed APK ]
                                                                                │
                                                                                ▼
                                                                  Embeds Public Certificate
                                                                  & v2/v3 Block Signatures
```

### What is Digital Code Signing?
Code signing uses asymmetric cryptography to bind the application binary to a specific author:
* **The Private Key:** Kept secret by the developer. Used by `apksigner` to compute cryptographic hashes of every file in the APK and encrypt those hashes into a digital signature.
* **The Public Certificate:** Embedded inside the APK. The user's Android device uses this certificate to decrypt and verify the signature during installation.

### Debug APK vs. Signed Release APK

| Metric | Debug APK (`app-debug.apk`) | Signed Release APK (`healthaware-v1.0.apk`) |
| :--- | :--- | :--- |
| **Signing Key** | Generic, insecure `androiddebugkey` | Custom cryptographic Keystore |
| **`android:debuggable`** | Set to `true` (allows external memory attach) | Set to `false` (hardened against debugger injection) |
| **Code Optimization** | Unoptimized, includes debug symbols | Optimized, stripped, production bytecode |
| **Security Risk** | High (anyone can impersonate the debug key) | Low (only holder of private keystore can update) |
| **Production Use** | Local development & testing only | **Mandatory for public distribution** |

### APK Signature Scheme v2 & v3
HealthAware is signed using modern **APK Signature Scheme v2 and v3**:
* Unlike legacy JAR signing (v1), which only verified individual files inside the ZIP, v2/v3 signs the entire binary file as a continuous sequence of bytes.
* If even a single byte of the APK is altered after signing (e.g., modifying `AndroidManifest.xml` or injecting tracking code), the signature verification fails and Android refuses to install the application.

---

## 8. Cryptographic Checksum & SHA-256 Verification

### What is a SHA-256 Checksum?
A **SHA-256 Checksum** is a 256-bit (64-character hexadecimal) cryptographic hash generated by processing every single byte of the APK file through the SHA-256 mathematical algorithm.

* **Deterministic:** Running the hash algorithm on the official file always outputs the exact same string.
* **Collision-Resistant:** It is computationally impossible to alter the APK without changing the resulting hash string.

### Official HealthAware Release Checksums
- **v1.1 (Current):** `12864C1AF451207940DE9C8353F7F41E9A2A8F4793F555AD43B95714B61B28B8` (healthaware-v1.1.apk)
- **v1.0 (Legacy):** `74CC4F548F33A56F15A290880CA3C82693A1402E881DB05B16B3BD58C690C40D` (healthaware-v1.0.apk)

### How Users Can Verify Integrity Before Installing

#### On Windows (PowerShell or Command Prompt):
```powershell
certutil -hashfile healthaware-v1.1.apk SHA256
```

#### On Linux or macOS (Terminal):
```bash
sha256sum healthaware-v1.1.apk
```

#### Verification Result:
If the terminal output matches `12864C1AF451207940DE9C8353F7F41E9A2A8F4793F555AD43B95714B61B28B8`, the user is 100% guaranteed that the APK is authentic, complete, and free from tampering or download corruption.

---

### Troubleshooting: "App not installed" Error
If Android displays **"App not installed"** when tapping the downloaded APK, the root causes and resolutions are:
1. **Signature Mismatch (`INSTALL_FAILED_UPDATE_INCOMPATIBLE`)**:
   - If an existing development/debug build (or an older APK signed with a different key) is already on the device, Android strictly refuses to overwrite it for security reasons.
   - **Fix:** Long-press the HealthAware app icon on your phone and select **Uninstall**. Then tap the newly downloaded APK to install fresh.
2. **"Install Unknown Apps" Blocked**:
   - On Android 8.0+, browser downloads require per-app installation permission.
   - **Fix:** On the prompt, tap **Settings** → toggle **Allow from this source** → tap Back and install.
3. **Play Protect Warning**:
   - Since HealthAware is an independent open-source release, Google Play Protect displays *"Unrecognized app"*.
   - **Fix:** Tap **More details** → **Install anyway**.

---

## 9. Android Sideloading, Unknown Sources & Play Protect

### What is Sideloading?
**Sideloading** refers to installing an Android application package (`.apk`) directly onto a smartphone via a web browser, file manager, or USB transfer, rather than downloading it through the Google Play Store.

### Why Direct Sideloading for Public Health?
1. **Immediate Community Accessibility:** Bypasses commercial store account requirements, country restrictions, and Google Play account sign-in requirements.
2. **Bandwidth Efficiency:** Allows community health workers to share the APK offline via local Wi-Fi or Bluetooth (Nearby Share) in remote clinics with zero internet access.
3. **Open-Source Transparency:** Users inspect the exact binary checksum against the repository's open release manifest.

### The "Install Unknown Apps" Permission Gate
Starting in Android 8.0 (API 26), Google replaced the global "Allow Unknown Sources" setting with a **per-app security permission**:
* When a user downloads `healthaware-v1.0.apk` using Chrome, Chrome does not have permission to trigger an installation by default.
* Android displays a prompt: *"For your security, your phone is not allowed to install unknown apps from this source."*
* **Procedure to Allow:**
  1. Tap **Settings** on the prompt.
  2. Toggle **Allow from this source** to ON for the browser (Chrome / Edge / Firefox).
  3. Tap **Back** and proceed with the installation.

### The Google Play Protect Prompt
When installing an application outside Google Play, Google's built-in scanner (**Play Protect**) may display a warning:
> *"Unrecognized app: Play Protect doesn't recognize this app's developer."*

#### Why Does This Appear?
* Google Play Protect maintains a cloud database of applications that have been installed millions of times from the Play Store.
* Because HealthAware is a direct, independent open-source release, Google Play has not indexed its cryptographic certificate signature in its commercial reputation database.
* **How Users Proceed:**
  1. Tap **More details**.
  2. Tap **Install anyway**.
  3. The app installs securely, backed by its verified SHA-256 checksum and Android's native Linux user sandbox.

---

## 10. The Static Release Manifest Contract (`version.json`)

To ensure the web download portal never advertises an unverified or corrupt binary, the frontend queries a static contract at `/download/version.json`:

```json
{
  "applicationId": "org.healthaware.app",
  "appName": "HealthAware",
  "versionName": "1.0",
  "versionCode": 1,
  "minAndroidVersion": "Android 7.0 (API 24)",
  "targetAndroidVersion": "Android 16 (API 36)",
  "fileName": "healthaware-v1.0.apk",
  "downloadUrl": "/download/healthaware-v1.0.apk",
  "fileSizeBytes": 11563957,
  "fileSizeFormatted": "11.0 MB",
  "sha256": "74CC4F548F33A56F15A290880CA3C82693A1402E881DB05B16B3BD58C690C40D",
  "releaseDate": "2026-10-25",
  "isAvailable": true,
  "status": "published",
  "statusMessage": "Official signed release build v1.0 is verified and available for direct download.",
  "requiresManualPermission": true
}
```

### Client-Side Integrity Enforcement
Before rendering the download button, Angular's [`validateReleaseManifest`](file:///c:/Users/nalli/project-internship/health-awareness/frontend/src/app/models/app-release.models.ts#L46-L80) validates that:
1. `applicationId` matches strictly `'org.healthaware.app'`.
2. `isAvailable` is only `true` when `status` is `'published'` (or `'ready'`).
3. `fileSizeBytes` is positive and does not exceed Cloudflare's 25 MiB limit.
4. `sha256` is a valid 64-character hexadecimal string.
5. `downloadUrl` begins with `/download/` and targets a `.apk` binary.

If any check fails, the UI fails closed, alerting the user and preventing the download of an incomplete or unverified binary.
