import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ComingSoonService {
  readonly message = signal<string | null>(null);
  private timer: ReturnType<typeof setTimeout> | null = null;

  show(featureName: string): void {
    if (this.timer) {
      clearTimeout(this.timer);
    }
    this.message.set(featureName);
    this.timer = setTimeout(() => {
      this.message.set(null);
      this.timer = null;
    }, 4000);
  }

  dismiss(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.message.set(null);
  }
}
