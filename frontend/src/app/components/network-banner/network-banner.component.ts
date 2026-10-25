import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NetworkStatusService } from '../../services/network-status.service';

@Component({
  selector: 'ha-network-banner',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './network-banner.component.html',
  styleUrl: './network-banner.component.css',
})
export class NetworkBannerComponent {
  readonly networkStatus = inject(NetworkStatusService);
  readonly checking = signal<boolean>(false);
  readonly dismissed = signal<boolean>(false);

  async retryConnection(): Promise<void> {
    this.checking.set(true);
    try {
      await this.networkStatus.checkReachability();
    } finally {
      this.checking.set(false);
    }
  }

  dismiss(): void {
    this.dismissed.set(true);
  }
}
