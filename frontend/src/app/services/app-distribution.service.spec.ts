import { describe, it, expect, vi, beforeEach } from 'vitest';
import { of, throwError, firstValueFrom } from 'rxjs';
import { AppDistributionService } from './app-distribution.service';
import {
  AppReleaseManifest,
  validateReleaseManifest,
} from '../models/app-release.models';

describe('AppDistributionService & Manifest Validation', () => {
  describe('validateReleaseManifest()', () => {
    it('validates a pending release manifest successfully', () => {
      const pendingManifest: AppReleaseManifest = {
        applicationId: 'org.healthaware.app',
        appName: 'HealthAware',
        versionName: '1.0',
        versionCode: 1,
        minAndroidVersion: 'Android 7.0 (API 24)',
        targetAndroidVersion: 'Android 16 (API 36)',
        fileName: 'healthaware-v1.0.apk',
        downloadUrl: '/download/healthaware-v1.0.apk',
        fileSizeBytes: null,
        fileSizeFormatted: null,
        sha256: null,
        releaseDate: null,
        isAvailable: false,
        status: 'signing_pending',
        statusMessage: 'Signing pending',
        requiresManualPermission: true,
      };

      const result = validateReleaseManifest(pendingManifest);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('validates an active published release manifest with valid checksum and size', () => {
      const publishedManifest: AppReleaseManifest = {
        applicationId: 'org.healthaware.app',
        appName: 'HealthAware',
        versionName: '1.0',
        versionCode: 1,
        minAndroidVersion: 'Android 7.0 (API 24)',
        targetAndroidVersion: 'Android 16 (API 36)',
        fileName: 'healthaware-v1.0.apk',
        downloadUrl: '/download/healthaware-v1.0.apk',
        fileSizeBytes: 10519794,
        fileSizeFormatted: '10.03 MB',
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        releaseDate: '2026-10-24',
        isAvailable: true,
        status: 'published',
        statusMessage: 'Official release ready for download',
        requiresManualPermission: true,
      };

      const result = validateReleaseManifest(publishedManifest);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('rejects manifest with mismatched applicationId', () => {
      const bad = {
        applicationId: 'com.malicious.app',
        versionName: '1.0',
        versionCode: 1,
        status: 'signing_pending',
        isAvailable: false,
      };
      const result = validateReleaseManifest(bad);
      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain("Invalid applicationId: expected 'org.healthaware.app'");
    });

    it('rejects an available release if file size exceeds Cloudflare Pages 25 MiB limit', () => {
      const oversized: AppReleaseManifest = {
        applicationId: 'org.healthaware.app',
        appName: 'HealthAware',
        versionName: '1.0',
        versionCode: 1,
        minAndroidVersion: 'Android 7.0 (API 24)',
        targetAndroidVersion: 'Android 16 (API 36)',
        fileName: 'healthaware-v1.0.apk',
        downloadUrl: '/download/healthaware-v1.0.apk',
        fileSizeBytes: 27 * 1024 * 1024, // 27 MiB > 25 MiB
        fileSizeFormatted: '27 MB',
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        releaseDate: '2026-10-24',
        isAvailable: true,
        status: 'published',
        statusMessage: 'Release',
        requiresManualPermission: true,
      };

      const result = validateReleaseManifest(oversized);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('exceeds Cloudflare Pages limit of 25 MiB'))).toBe(true);
    });

    it('rejects an available release if SHA-256 checksum is malformed or missing', () => {
      const invalidSha: AppReleaseManifest = {
        applicationId: 'org.healthaware.app',
        appName: 'HealthAware',
        versionName: '1.0',
        versionCode: 1,
        minAndroidVersion: 'Android 7.0 (API 24)',
        targetAndroidVersion: 'Android 16 (API 36)',
        fileName: 'healthaware-v1.0.apk',
        downloadUrl: '/download/healthaware-v1.0.apk',
        fileSizeBytes: 10519794,
        fileSizeFormatted: '10.0 MB',
        sha256: 'not-a-valid-sha',
        releaseDate: '2026-10-24',
        isAvailable: true,
        status: 'published',
        statusMessage: 'Ready',
        requiresManualPermission: true,
      };

      const result = validateReleaseManifest(invalidSha);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('64-character SHA-256'))).toBe(true);
    });
  });

  describe('AppDistributionService', () => {
    let service: AppDistributionService;
    let mockHttp: any;

    beforeEach(() => {
      mockHttp = {
        get: vi.fn(),
      };
      service = new AppDistributionService(mockHttp as any);
    });

    it('fetches and stores manifest when getManifest() is called', async () => {
      const sampleManifest: AppReleaseManifest = {
        applicationId: 'org.healthaware.app',
        appName: 'HealthAware',
        versionName: '1.0',
        versionCode: 1,
        minAndroidVersion: 'Android 7.0 (API 24)',
        targetAndroidVersion: 'Android 16 (API 36)',
        fileName: 'healthaware-v1.0.apk',
        downloadUrl: '/download/healthaware-v1.0.apk',
        fileSizeBytes: null,
        fileSizeFormatted: null,
        sha256: null,
        releaseDate: null,
        isAvailable: false,
        status: 'signing_pending',
        statusMessage: 'Pending release key setup',
        requiresManualPermission: true,
      };

      mockHttp.get.mockReturnValue(of(sampleManifest));

      const manifest = await firstValueFrom(service.getManifest());
      expect(manifest).toEqual(sampleManifest);
      expect(service.manifest()).toEqual(sampleManifest);
      expect(service.isLoading()).toBe(false);
      expect(service.errorMessage()).toBeNull();
    });

    it('handles manifest fetch error gracefully', async () => {
      mockHttp.get.mockReturnValue(throwError(() => new Error('Network failure')));

      const manifest = await firstValueFrom(service.getManifest());
      expect(manifest).toBeNull();
      expect(service.manifest()).toBeNull();
      expect(service.isLoading()).toBe(false);
      expect(service.errorMessage()).toContain('Network failure');
    });

    it('opens and closes the modal and manages state signals', () => {
      mockHttp.get.mockReturnValue(of({
        applicationId: 'org.healthaware.app',
        appName: 'HealthAware',
        versionName: '1.0',
        versionCode: 1,
        minAndroidVersion: 'Android 7.0 (API 24)',
        targetAndroidVersion: 'Android 16 (API 36)',
        fileName: 'healthaware-v1.0.apk',
        downloadUrl: '/download/healthaware-v1.0.apk',
        fileSizeBytes: null,
        fileSizeFormatted: null,
        sha256: null,
        releaseDate: null,
        isAvailable: false,
        status: 'signing_pending',
        statusMessage: 'Pending',
        requiresManualPermission: true,
      }));

      expect(service.isOpen()).toBe(false);
      service.openModal();
      expect(service.isOpen()).toBe(true);

      service.closeModal();
      expect(service.isOpen()).toBe(false);
    });
  });
});
