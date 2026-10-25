/**
 * Type definitions and manifest validation contracts for HealthAware Android direct distribution.
 */

export type ReleaseStatus = 'published' | 'ready' | 'signing_pending' | 'unavailable';

export interface AppReleaseManifest {
  /** Android application package ID (must match build.gradle applicationId) */
  applicationId: string;
  /** Human-readable application name */
  appName: string;
  /** SemVer-compatible version string */
  versionName: string;
  /** Monotonically increasing version integer */
  versionCode: number;
  /** Minimum supported Android operating system version */
  minAndroidVersion: string;
  /** Target Android operating system version */
  targetAndroidVersion: string;
  /** Versioned filename of the APK asset */
  fileName: string;
  /** Public download URL relative to the site root */
  downloadUrl: string;
  /** Exact APK file size in bytes, or null if pending release */
  fileSizeBytes: number | null;
  /** User-friendly formatted file size (e.g. '10.0 MB'), or null if pending */
  fileSizeFormatted: string | null;
  /** Hex-encoded SHA-256 cryptographic checksum, or null if pending */
  sha256: string | null;
  /** Release publication date (YYYY-MM-DD), or null if pending */
  releaseDate: string | null;
  /** Whether the APK is cryptographically signed, verified, and available for download */
  isAvailable: boolean;
  /** Operational release readiness status */
  status: ReleaseStatus;
  /** Plain-language explanation of availability or pending prerequisites */
  statusMessage: string;
  /** Whether manual installation / sideloading permission is required on Android */
  requiresManualPermission: boolean;
}

/**
 * Validates the cryptographic and distribution integrity of a release manifest.
 * Ensures the manifest cannot advertise a missing, unsigned, or corrupt APK.
 */
export function validateReleaseManifest(manifest: unknown): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!manifest || typeof manifest !== 'object') {
    return { valid: false, errors: ['Manifest is empty or not a valid object'] };
  }

  const m = manifest as Partial<AppReleaseManifest>;

  if (m.applicationId !== 'org.healthaware.app') {
    errors.push(`Invalid applicationId: expected 'org.healthaware.app', got '${m.applicationId}'`);
  }

  if (!m.versionName || typeof m.versionName !== 'string') {
    errors.push('Missing or invalid versionName');
  }

  if (typeof m.versionCode !== 'number' || m.versionCode < 1) {
    errors.push('Missing or invalid versionCode (must be positive integer)');
  }

  if (!m.status || !['published', 'ready', 'signing_pending', 'unavailable'].includes(m.status)) {
    errors.push(`Invalid release status: '${m.status}'`);
  }

  // If marked as available for public download, enforce strict release artifact verification
  if (m.isAvailable === true) {
    if (m.status !== 'published' && m.status !== 'ready') {
      errors.push('isAvailable is true but status is not "published"');
    }

    if (!m.fileName || !m.fileName.endsWith('.apk')) {
      errors.push('Available release must have a valid .apk fileName');
    }

    if (!m.downloadUrl || !m.downloadUrl.startsWith('/download/')) {
      errors.push('Available release must specify a versioned /download/ URL');
    }

    if (typeof m.fileSizeBytes !== 'number' || m.fileSizeBytes <= 0) {
      errors.push('Available release must specify positive fileSizeBytes');
    } else {
      // Cloudflare Pages hard limit: 25 MiB (26,214,400 bytes)
      const MAX_PAGES_FILE_SIZE = 25 * 1024 * 1024;
      if (m.fileSizeBytes > MAX_PAGES_FILE_SIZE) {
        errors.push(
          `APK file size (${m.fileSizeBytes} bytes) exceeds Cloudflare Pages limit of 25 MiB (${MAX_PAGES_FILE_SIZE} bytes)`
        );
      }
    }

    // SHA-256 must be a 64-character hexadecimal string
    const sha256Regex = /^[a-fA-F0-9]{64}$/;
    if (!m.sha256 || !sha256Regex.test(m.sha256)) {
      errors.push('Available release must provide a valid 64-character SHA-256 hexadecimal checksum');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
