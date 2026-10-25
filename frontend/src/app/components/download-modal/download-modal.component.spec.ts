import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DownloadModalComponent } from './download-modal.component';
import { AppDistributionService } from '../../services/app-distribution.service';
import { AppReleaseManifest } from '../../models/app-release.models';
import { signal } from '@angular/core';

describe('DownloadModalComponent', () => {
  let fixture: ComponentFixture<DownloadModalComponent>;
  let component: DownloadModalComponent;
  let mockDistributionService: {
    isOpen: ReturnType<typeof signal<boolean>>;
    manifest: ReturnType<typeof signal<AppReleaseManifest | null>>;
    isLoading: ReturnType<typeof signal<boolean>>;
    errorMessage: ReturnType<typeof signal<string | null>>;
    copiedSha: ReturnType<typeof signal<boolean>>;
    closeModal: ReturnType<typeof vi.fn>;
    copySha256: ReturnType<typeof vi.fn>;
  };

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
    statusMessage: 'Official release signing key setup is in progress.',
    requiresManualPermission: true,
  };

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
    fileSizeFormatted: '10.0 MB',
    sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    releaseDate: '2026-10-24',
    isAvailable: true,
    status: 'published',
    statusMessage: 'Official release ready for download',
    requiresManualPermission: true,
  };

  beforeEach(async () => {
    mockDistributionService = {
      isOpen: signal(false),
      manifest: signal(null),
      isLoading: signal(false),
      errorMessage: signal(null),
      copiedSha: signal(false),
      closeModal: vi.fn(),
      copySha256: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [DownloadModalComponent],
      providers: [
        { provide: AppDistributionService, useValue: mockDistributionService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DownloadModalComponent);
    component = fixture.componentInstance;
  });

  it('renders nothing when modal is closed', () => {
    fixture.detectChanges();
    const modal = fixture.nativeElement.querySelector('.ha-modal-backdrop');
    expect(modal).toBeNull();
  });

  it('renders accessible modal dialog when isOpen is true', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(pendingManifest);
    fixture.detectChanges();

    const dialog = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.getAttribute('aria-labelledby')).toBe('download-modal-title');
  });

  it('displays signing-pending state and disabled button when isAvailable is false', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(pendingManifest);
    fixture.detectChanges();

    const pendingCard = fixture.nativeElement.querySelector('#signing-pending-card');
    expect(pendingCard).not.toBeNull();
    expect(pendingCard.textContent).toContain('Cryptographic Signing Pending');
    expect(pendingCard.textContent).toContain('org.healthaware.app');

    const disabledBtn = fixture.nativeElement.querySelector('#btn-download-pending');
    expect(disabledBtn).not.toBeNull();
    expect(disabledBtn.disabled).toBe(true);

    // Ensure no active download link is advertised
    const activeDownloadLink = fixture.nativeElement.querySelector('#btn-download-apk');
    expect(activeDownloadLink).toBeNull();
  });

  it('displays download link, file size and SHA-256 checksum when isAvailable is true', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(publishedManifest);
    fixture.detectChanges();

    const downloadLink = fixture.nativeElement.querySelector('#btn-download-apk');
    expect(downloadLink).not.toBeNull();
    expect(downloadLink.getAttribute('href')).toBe('/download/healthaware-v1.0.apk');
    expect(downloadLink.textContent).toContain('10.0 MB');

    const shaDisplay = fixture.nativeElement.querySelector('#display-sha256');
    expect(shaDisplay).not.toBeNull();
    expect(shaDisplay.textContent).toContain('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
  });

  it('calls closeModal when close button is clicked', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(pendingManifest);
    fixture.detectChanges();

    const closeBtn = fixture.nativeElement.querySelector('#download-modal-close');
    closeBtn.click();
    expect(mockDistributionService.closeModal).toHaveBeenCalled();
  });

  it('calls closeModal when clicking the backdrop', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(pendingManifest);
    fixture.detectChanges();

    const backdrop = fixture.nativeElement.querySelector('.ha-modal-backdrop');
    backdrop.click();
    expect(mockDistributionService.closeModal).toHaveBeenCalled();
  });

  it('calls closeModal when Escape key is pressed', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(pendingManifest);
    fixture.detectChanges();

    component.onEscapeKey();
    expect(mockDistributionService.closeModal).toHaveBeenCalled();
  });

  it('displays loading spinner and status when isLoading is true', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.isLoading.set(true);
    fixture.detectChanges();

    const loadingElem = fixture.nativeElement.querySelector('.ha-loading-state');
    expect(loadingElem).not.toBeNull();
    expect(loadingElem.getAttribute('role')).toBe('status');
    expect(loadingElem.textContent).toContain('Loading distribution manifest...');
  });

  it('displays error notice safely when errorMessage is present', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.errorMessage.set('Failed to fetch version manifest');
    fixture.detectChanges();

    const errorAlert = fixture.nativeElement.querySelector('.ha-alert-error');
    expect(errorAlert).not.toBeNull();
    expect(errorAlert.getAttribute('role')).toBe('alert');
    expect(errorAlert.textContent).toContain('Failed to fetch version manifest');
    // Ensure no download button is present
    expect(fixture.nativeElement.querySelector('#btn-download-apk')).toBeNull();
  });

  it('triggers copyChecksum when copy button is clicked', () => {
    mockDistributionService.isOpen.set(true);
    mockDistributionService.manifest.set(publishedManifest);
    fixture.detectChanges();

    const copyBtn = fixture.nativeElement.querySelector('#btn-copy-sha256');
    copyBtn.click();
    expect(mockDistributionService.copySha256).toHaveBeenCalledWith(publishedManifest.sha256);
  });
});
