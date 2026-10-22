import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';
import { SecureStorage } from '@aparajita/capacitor-secure-storage';

/**
 * Hardware-backed secure storage for sensitive authentication tokens on Android.
 * - On Native Android: Uses Android Keystore backed storage via SecureStorage.
 * - On Web Browser: Preserves standard localStorage behavior.
 * - Never silently falls back to plaintext storage on native failure.
 */
@Injectable({ providedIn: 'root' })
export class SecureStorageService {
  private readonly isNative = Capacitor.isNativePlatform();

  async setItem(key: string, value: string): Promise<void> {
    if (this.isNative) {
      try {
        await SecureStorage.set(key, value);
      } catch (err) {
        console.error('Failed to securely store credential in Android Keystore');
        throw new Error('SECURE_STORAGE_SET_FAILED');
      }
    } else {
      localStorage.setItem(key, value);
    }
  }

  async getItem(key: string): Promise<string | null> {
    if (this.isNative) {
      try {
        const val = await SecureStorage.get(key);
        if (val === null || val === undefined) return null;
        return typeof val === 'string' ? val : JSON.stringify(val);
      } catch (err) {
        console.error('Failed to retrieve credential from Android Keystore');
        return null;
      }
    } else {
      return localStorage.getItem(key);
    }
  }

  async removeItem(key: string): Promise<void> {
    if (this.isNative) {
      try {
        await SecureStorage.remove(key);
      } catch (err) {
        console.error('Failed to remove credential from Android Keystore');
      }
    } else {
      localStorage.removeItem(key);
    }
  }

  async clear(): Promise<void> {
    if (this.isNative) {
      try {
        await SecureStorage.clear();
      } catch (err) {
        console.error('Failed to clear credentials from Android Keystore');
      }
    } else {
      localStorage.clear();
    }
  }
}
