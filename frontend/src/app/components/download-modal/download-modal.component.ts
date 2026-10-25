import {
  Component,
  HostListener,
  inject,
  ElementRef,
  ViewChild,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppDistributionService } from '../../services/app-distribution.service';

@Component({
  selector: 'ha-download-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './download-modal.component.html',
  styleUrls: ['./download-modal.component.css'],
})
export class DownloadModalComponent {
  readonly distribution = inject(AppDistributionService);

  @ViewChild('modalCloseBtn') modalCloseBtn?: ElementRef<HTMLButtonElement>;

  constructor() {
    // Focus close button on modal open for keyboard accessibility
    effect(() => {
      if (this.distribution.isOpen()) {
        setTimeout(() => {
          this.modalCloseBtn?.nativeElement?.focus();
        }, 50);
      }
    });
  }

  @HostListener('document:keydown.escape')
  onEscapeKey(): void {
    if (this.distribution.isOpen()) {
      this.close();
    }
  }

  close(): void {
    this.distribution.closeModal();
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('ha-modal-backdrop')) {
      this.close();
    }
  }

  async copyChecksum(checksum: string | null): Promise<void> {
    if (!checksum) return;
    await this.distribution.copySha256(checksum);
  }
}
