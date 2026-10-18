import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ConcernService, ConcernSubmitResponse } from '../../services/concern.service';

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

  requestGps() {
    if (!navigator.geolocation) {
      this.errorMessage.set('Geolocation is not supported by your browser.');
      return;
    }
    this.gpsLocating.set(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.latitude.set(pos.coords.latitude);
        this.longitude.set(pos.coords.longitude);
        this.gpsLocating.set(false);
      },
      () => {
        this.gpsLocating.set(false);
        this.errorMessage.set('Unable to retrieve location. Please fill locality details manually.');
      },
      { timeout: 10000 }
    );
  }

  onPhotoSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      if (file.size > 5 * 1024 * 1024) {
        this.errorMessage.set('Photo size must not exceed 5 MB.');
        return;
      }
      this.selectedPhoto.set(file);
      const reader = new FileReader();
      reader.onload = (e) => this.photoPreview.set(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  }

  removePhoto() {
    this.selectedPhoto.set(null);
    this.photoPreview.set(null);
  }

  submitReport() {
    this.submitting.set(true);
    this.errorMessage.set(null);

    const mun = this.municipalityNotSure() ? 'Not sure' : this.municipality().trim();

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
        photo: this.selectedPhoto() || undefined,
      })
      .subscribe({
        next: (res) => {
          this.submitting.set(false);
          this.submissionResult.set(res);
          this.currentStep.set(5); // Confirmation screen
        },
        error: (err) => {
          this.submitting.set(false);
          const msg = err.error?.error?.message || 'Submission failed. Please check your network and try again.';
          this.errorMessage.set(msg);
        },
      });
  }

  copyCredentials() {
    const res = this.submissionResult();
    if (!res) return;
    const text = `HealthAware Concern Reference: ${res.data.reference_id}\nPrivate Tracking Token: ${res.data.tracking_token}\nTrack at: ${window.location.origin}/track`;
    navigator.clipboard.writeText(text).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 3000);
    });
  }

  printConfirmation() {
    window.print();
  }

  getCategoryLabel(id: string): string {
    const c = this.categories.find((x) => x.id === id);
    return c ? c.title : id;
  }
}
