import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, tap, catchError, map } from 'rxjs';
import {
  AppReleaseManifest,
  validateReleaseManifest,
} from '../models/app-release.models';

@Injectable({
  providedIn: 'root',
})
export class AppDistributionService {
  readonly isOpen = signal<boolean>(false);
  readonly manifest = signal<AppReleaseManifest | null>(null);
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly copiedSha = signal<boolean>(false);

  constructor(private http: HttpClient) {}

  /**
   * Fetches and validates the static version manifest.
   * Caches in-memory to prevent redundant network round-trips.
   */
  getManifest(): Observable<AppReleaseManifest | null> {
    const existing = this.manifest();
    if (existing) {
      return of(existing);
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    // Fetch static manifest from public download directory
    return this.http.get<AppReleaseManifest>('/download/version.json').pipe(
      map((rawManifest) => {
        const validation = validateReleaseManifest(rawManifest);
        if (!validation.valid) {
          throw new Error(`Manifest integrity check failed: ${validation.errors.join(', ')}`);
        }
        return rawManifest;
      }),
      tap((validManifest) => {
        this.manifest.set(validManifest);
        this.isLoading.set(false);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        const msg = err?.message || 'Unable to load release information.';
        this.errorMessage.set(msg);
        return of(null);
      })
    );
  }

  /**
   * Opens the download and release readiness modal.
   */
  openModal(): void {
    this.isOpen.set(true);
    this.copiedSha.set(false);
    if (!this.manifest()) {
      this.getManifest().subscribe();
    }
  }

  /**
   * Closes the download modal.
   */
  closeModal(): void {
    this.isOpen.set(false);
    this.copiedSha.set(false);
  }

  /**
   * Copies the SHA-256 checksum to user clipboard with fallback.
   */
  async copySha256(checksum: string): Promise<boolean> {
    if (!checksum) return false;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(checksum);
        this.copiedSha.set(true);
        setTimeout(() => this.copiedSha.set(false), 3000);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }
}
