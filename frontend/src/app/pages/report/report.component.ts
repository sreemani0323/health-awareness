import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Capacitor } from '@capacitor/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Geolocation } from '@capacitor/geolocation';
import { ConcernService, ConcernSubmitResponse } from '../../services/concern.service';
import { getActionableErrorMessage } from '../../interceptors/api-timeout-retry.interceptor';

interface CategoryOption {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
}

@Component({
  selector: 'app-report',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './report.component.html',
  styleUrls: ['./report.component.css'],
})
export class ReportConcernComponent {
  private concernService = inject(ConcernService);
  private router = inject(Router);

  readonly isNative = signal<boolean>(Capacitor.isNativePlatform());

  currentStep = signal<number>(1);
  submitting = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  copied = signal<boolean>(false);

  // Form State
  selectedCategory = signal<string>('stagnant_water');
  state = signal<string>('Andhra Pradesh');
  district = signal<string>('');
  municipality = signal<string>('');
  municipalityNotSure = signal<boolean>(false);
  locality = signal<string>('');
  latitude = signal<number | null>(null);
  longitude = signal<number | null>(null);
  gpsLocating = signal<boolean>(false);

  description = signal<string>('');
  duration = signal<string>('< 3 days');

  // Multi-photo evidence state (up to 5 images)
  readonly MAX_PHOTOS = 5;
  readonly MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
  selectedPhotos = signal<File[]>([]);
  photoPreviews = signal<string[]>([]);

  // Backward-compatible signals for legacy single-photo tests
  selectedPhoto = signal<File | null>(null);
  photoPreview = signal<string | null>(null);

  // Submission Result
  submissionResult = signal<ConcernSubmitResponse | null>(null);

  categories: CategoryOption[] = [
    {
      id: 'garbage',
      title: 'Accumulated Garbage or Missed Waste',
      subtitle: 'Trash heaps, uncollected roadside waste, or overflowing bins.',
      icon: '🗑️',
    },
    {
      id: 'stagnant_water',
      title: 'Stagnant Water / Mosquito Breeding Site',
      subtitle: 'Water puddles, open storage tanks, or blocked ditches harboring mosquitoes.',
      icon: '🦟',
    },
    {
      id: 'drainage',
      title: 'Blocked Drains or Sewage Overflow',
      subtitle: 'Clogged open gutters, wastewater spillage, or drain blockages.',
      icon: '🚰',
    },
    {
      id: 'sanitation',
      title: 'Poor Public-Toilet Sanitation',
      subtitle: 'Unsanitary municipal facilities, broken toilets, or hygiene hazards.',
      icon: '🚻',
    },
  ];

  durations: string[] = ['< 3 days', '3-7 days', '1-2 weeks', '> 1 month'];

  selectCategory(id: string) {
    this.selectedCategory.set(id);
  }

  nextStep() {
    this.errorMessage.set(null);
    if (this.currentStep() === 1) {
      if (!this.selectedCategory()) {
        this.errorMessage.set('Please select a concern category.');
        return;
      }
      this.currentStep.set(2);
    } else if (this.currentStep() === 2) {
      if (!this.district().trim()) {
        this.errorMessage.set('Please enter or select a district.');
        return;
      }
      if (!this.locality().trim()) {
        this.errorMessage.set('Please specify the locality, street, or landmark.');
        return;
      }
      this.currentStep.set(3);
    } else if (this.currentStep() === 3) {
      if (!this.description().trim()) {
        this.errorMessage.set('Please provide a short description of the problem.');
        return;
      }
      this.currentStep.set(4);
    }
  }

  prevStep() {
    this.errorMessage.set(null);
    if (this.currentStep() > 1) {
      this.currentStep.update((s) => s - 1);
    }
  }

  async requestGps(): Promise<void> {
    this.gpsLocating.set(true);
    this.errorMessage.set(null);

    try {
      if (Capacitor.isNativePlatform()) {
        const permStatus = await Geolocation.checkPermissions();
        if (permStatus.location === 'denied') {
          const reqStatus = await Geolocation.requestPermissions();
          if (reqStatus.location === 'denied') {
            this.gpsLocating.set(false);
            this.errorMessage.set(
              'Location permission was denied. You can still enter your district and locality details manually.'
            );
            return;
          }
        }

        const position = await Geolocation.getCurrentPosition({
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000,
        });

        this.latitude.set(position.coords.latitude);
        this.longitude.set(position.coords.longitude);
        this.gpsLocating.set(false);
      } else {
        if (!navigator.geolocation) {
          this.gpsLocating.set(false);
          this.errorMessage.set('Geolocation is not supported by your browser. Please enter locality details manually.');
          return;
        }

        navigator.geolocation.getCurrentPosition(
          (pos) => {
            this.latitude.set(pos.coords.latitude);
            this.longitude.set(pos.coords.longitude);
            this.gpsLocating.set(false);
          },
          (err) => {
            this.gpsLocating.set(false);
            let msg = 'Unable to retrieve location. Please fill locality details manually.';
            if (err.code === err.PERMISSION_DENIED) {
              msg = 'Location permission was denied in your browser. Please enter details manually.';
            } else if (err.code === err.TIMEOUT) {
              msg = 'Location request timed out. Please enter locality details manually.';
            } else if (err.code === err.POSITION_UNAVAILABLE) {
              msg = 'Location service is unavailable on your device. Please enter details manually.';
            }
            this.errorMessage.set(msg);
          },
          { timeout: 10000, enableHighAccuracy: true, maximumAge: 60000 }
        );
      }
    } catch (err: any) {
      this.gpsLocating.set(false);
      let msg = 'Could not retrieve device location. Please enter locality details manually.';
      const errMsg = err?.message || '';
      if (errMsg.includes('denied')) {
        msg = 'Location permission was denied. You can enter locality details manually.';
      } else if (errMsg.includes('disabled') || errMsg.includes('location services are not enabled')) {
        msg = 'Location services are disabled on your device. Please enable GPS in device Settings or enter locality manually.';
      } else if (errMsg.includes('timeout')) {
        msg = 'Location request timed out. Please enter locality details manually.';
      }
      this.errorMessage.set(msg);
    }
  }

  onPhotosSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const files = Array.from(input.files);
    this.addPhotos(files);
    input.value = '';
  }

  // Legacy single photo event handler for backwards compatibility
  onPhotoSelected(event: Event): void {
    this.onPhotosSelected(event);
  }

  private addPhotos(files: File[]): void {
    const current = this.selectedPhotos();
    if (current.length + files.length > this.MAX_PHOTOS) {
      this.errorMessage.set(
        `You can attach at most ${this.MAX_PHOTOS} photos. You have already attached ${current.length}.`
      );
      return;
    }

    const validFiles: File[] = [];
    for (const file of files) {
      if (file.size > this.MAX_PHOTO_SIZE_BYTES) {
        this.errorMessage.set(`Photo "${file.name}" exceeds the 5 MB maximum size limit.`);
        return;
      }
      validFiles.push(file);
    }

    validFiles.forEach((f) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const previewUrl = e.target?.result as string;
        this.selectedPhotos.update((arr) => [...arr, f]);
        this.photoPreviews.update((arr) => [...arr, previewUrl]);
        const updated = this.selectedPhotos();
        this.selectedPhoto.set(updated[0] || null);
        this.photoPreview.set(this.photoPreviews()[0] || null);
      };
      reader.readAsDataURL(f);
    });
  }

  async captureNativePhoto(source: 'camera' | 'photos'): Promise<void> {
    if (this.selectedPhotos().length >= this.MAX_PHOTOS) {
      this.errorMessage.set(`You can attach a maximum of ${this.MAX_PHOTOS} photos.`);
      return;
    }

    try {
      this.errorMessage.set(null);
      const photo = await Camera.getPhoto({
        resultType: CameraResultType.Uri,
        source: source === 'camera' ? CameraSource.Camera : CameraSource.Photos,
        quality: 85,
        allowEditing: false,
      });

      if (photo.webPath) {
        const response = await fetch(photo.webPath);
        const blob = await response.blob();
        if (blob.size > this.MAX_PHOTO_SIZE_BYTES) {
          this.errorMessage.set('Captured photo size must not exceed 5 MB.');
          return;
        }
        const ext = photo.format || 'jpg';
        const file = new File(
          [blob],
          `concern_evidence_${Date.now()}_${this.selectedPhotos().length + 1}.${ext}`,
          { type: blob.type || `image/${ext}` }
        );

        this.selectedPhotos.update((arr) => [...arr, file]);
        this.photoPreviews.update((arr) => [...arr, photo.webPath!]);
        this.selectedPhoto.set(this.selectedPhotos()[0] || null);
        this.photoPreview.set(this.photoPreviews()[0] || null);
      }
    } catch (err: any) {
      if (err?.message && !err.message.includes('User cancelled')) {
        console.warn('Camera error:', err);
        this.errorMessage.set('Could not access camera/photos: ' + (err.message || 'Permission denied'));
      }
    }
  }

  removePhoto(index = 0): void {
    this.selectedPhotos.update((arr) => arr.filter((_, i) => i !== index));
    this.photoPreviews.update((arr) => arr.filter((_, i) => i !== index));
    const updated = this.selectedPhotos();
    this.selectedPhoto.set(updated[0] || null);
    this.photoPreview.set(this.photoPreviews()[0] || null);
  }

  submitReport(): void {
    if (!this.selectedCategory()) {
      this.errorMessage.set('Category is required. Please return to Step 1 to select one.');
      return;
    }
    if (!this.district().trim()) {
      this.errorMessage.set('District is required. Please return to Step 2 to enter a district.');
      return;
    }
    if (!this.locality().trim()) {
      this.errorMessage.set('Locality or landmark is required. Please return to Step 2.');
      return;
    }
    if (!this.description().trim()) {
      this.errorMessage.set('Description is required. Please return to Step 3.');
      return;
    }

    this.submitting.set(true);
    this.errorMessage.set(null);

    const mun = this.municipalityNotSure() ? 'Not sure' : this.municipality().trim();
    const photosToSend =
      this.selectedPhotos().length > 0
        ? this.selectedPhotos()
        : this.selectedPhoto()
          ? [this.selectedPhoto()!]
          : undefined;

    this.concernService
      .submitConcern({
        category: this.selectedCategory(),
        state: this.state(),
        district: this.district().trim(),
        municipality: mun || undefined,
        locality: this.locality().trim(),
        description: this.description().trim(),
        duration: this.duration(),
        latitude: this.latitude() || undefined,
        longitude: this.longitude() || undefined,
        photos: photosToSend,
        photo: photosToSend?.[0],
      })
      .subscribe({
        next: (res) => {
          this.submitting.set(false);
          this.submissionResult.set(res);
          this.currentStep.set(5); // Confirmation screen
        },
        error: (err) => {
          this.submitting.set(false);
          // Preserve all form input fields and attachment files/previews for retry
          const userMsg =
            err.error?.userMessage ||
            err.error?.error?.message ||
            getActionableErrorMessage(err);
          this.errorMessage.set(userMsg);
        },
      });
  }

  copyCredentials(): void {
    const res = this.submissionResult();
    if (!res) return;
    const text = `HealthAware Concern Reference: ${res.data.reference_id}\nPrivate Tracking Token: ${res.data.tracking_token}\nTrack at: ${window.location.origin}/track`;
    navigator.clipboard.writeText(text).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 3000);
    });
  }

  printConfirmation(): void {
    window.print();
  }

  getCategoryLabel(id: string): string {
    const c = this.categories.find((x) => x.id === id);
    return c ? c.title : id;
  }

  getCategorySubtitle(id: string): string {
    const c = this.categories.find((x) => x.id === id);
    return c ? c.subtitle : '';
  }
}

