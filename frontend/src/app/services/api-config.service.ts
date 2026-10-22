import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';
import { environment } from '../../environments/environment';

/**
 * Service to resolve API endpoints dynamically:
 * - On Native Android (Capacitor WebView): resolves against the HTTPS Cloudflare Pages API proxy.
 * - On Web Browser: preserves the standard relative '/api/v1' route.
 */
@Injectable({ providedIn: 'root' })
export class ApiConfigService {
  get apiBaseUrl(): string {
    if (Capacitor.isNativePlatform()) {
      return environment.androidApiBaseUrl || 'https://health-awareness.pages.dev/api/v1';
    }
    return environment.apiBaseUrl;
  }

  get isNative(): boolean {
    return Capacitor.isNativePlatform();
  }

  /**
   * Resolves an API sub-path to a full endpoint URL.
   * e.g. getApiUrl('/topics') -> 'https://health-awareness.pages.dev/api/v1/topics' on Android
   * or '/api/v1/topics' on Web.
   */
  getApiUrl(path: string): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const subPath = cleanPath.startsWith('/api/v1')
      ? cleanPath.substring('/api/v1'.length)
      : cleanPath;
    return `${this.apiBaseUrl}${subPath}`;
  }
}
