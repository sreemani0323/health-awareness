import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ReportConcernComponent } from './report.component';
import { ConcernService, ConcernSubmitResponse } from '../../services/concern.service';
import { HttpErrorResponse } from '@angular/common/http';

describe('ReportConcernComponent', () => {
  let component: ReportConcernComponent;
  let fixture: ComponentFixture<ReportConcernComponent>;
  let concernService: ConcernService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportConcernComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportConcernComponent);
    component = fixture.componentInstance;
    concernService = TestBed.inject(ConcernService);
    fixture.detectChanges();
  });

  it('should create the report concern component', () => {
    expect(component).toBeTruthy();
  });

  it('should start at step 1 with default category selected', () => {
    expect(component.currentStep()).toBe(1);
    expect(component.selectedCategory()).toBe('stagnant_water');
  });

  it('should advance to step 2 when category is selected', () => {
    component.selectCategory('garbage');
    component.nextStep();
    expect(component.currentStep()).toBe(2);
  });

  it('should require district and locality before advancing to step 3', () => {
    component.currentStep.set(2);
    component.district.set('');
    component.nextStep();
    expect(component.currentStep()).toBe(2);
    expect(component.errorMessage()).toContain('Please enter or select a district');

    component.district.set('Visakhapatnam');
    component.locality.set('');
    component.nextStep();
    expect(component.currentStep()).toBe(2);
    expect(component.errorMessage()).toContain('Please specify the locality');

    component.locality.set('RTC Complex');
    component.nextStep();
    expect(component.currentStep()).toBe(3);
  });

  it('should require description before advancing to step 4', () => {
    component.currentStep.set(3);
    component.description.set('');
    component.nextStep();
    expect(component.currentStep()).toBe(3);
    expect(component.errorMessage()).toContain('Please provide a short description');

    component.description.set('Overflowing garbage causing severe health hazard');
    component.nextStep();
    expect(component.currentStep()).toBe(4);
  });

  it('preserves form input and selected photo attachment when submission fails', () => {
    // Fill all form fields and attachment
    component.selectCategory('stagnant_water');
    component.district.set('Guntur');
    component.locality.set('Market Road');
    component.description.set('Stagnant cesspool breeding mosquitoes near school.');
    component.duration.set('3-7 days');

    const testFile = new File(['mock image data'], 'puddle.jpg', { type: 'image/jpeg' });
    component.selectedPhoto.set(testFile);
    component.currentStep.set(4);

    // Mock network failure / server unavailable
    const errorResponse = new HttpErrorResponse({
      status: 503,
      statusText: 'Service Unavailable',
      error: {
        userMessage: 'The service is temporarily unavailable. Please retry in a moment.',
      },
    });

    vi.spyOn(concernService, 'submitConcern').mockReturnValue(throwError(() => errorResponse));

    component.submitReport();
    fixture.detectChanges();

    // Verify submission failed gracefully
    expect(component.submitting()).toBe(false);
    expect(component.submissionResult()).toBeNull();
    // User remains on step 4 review
    expect(component.currentStep()).toBe(4);

    // Critical: ALL user inputs and attachments are preserved!
    expect(component.district()).toBe('Guntur');
    expect(component.locality()).toBe('Market Road');
    expect(component.description()).toBe('Stagnant cesspool breeding mosquitoes near school.');
    expect(component.duration()).toBe('3-7 days');
    expect(component.selectedPhoto()).toBe(testFile);

    // User is presented with clear, actionable message
    expect(component.errorMessage()).toContain('temporarily unavailable');
  });

  it('transitions to confirmation step 5 only upon confirmed server response', () => {
    component.selectCategory('drainage');
    component.district.set('Krishna');
    component.locality.set('Station Road');
    component.description.set('Blocked drainage overflowing onto pedestrian walkway.');
    component.currentStep.set(4);

    const mockSuccess: ConcernSubmitResponse = {
      message: 'Concern registered successfully',
      notice: 'Non-emergency public notice',
      data: {
        reference_id: 'HA-2026-TEST-REF',
        tracking_token: 'tok_test_secret_123',
        status: 'received',
        status_label: 'Received',
        created_at: new Date().toISOString(),
      },
    };

    vi.spyOn(concernService, 'submitConcern').mockReturnValue(of(mockSuccess));

    component.submitReport();
    fixture.detectChanges();

    expect(component.submitting()).toBe(false);
    expect(component.submissionResult()).toEqual(mockSuccess);
    expect(component.currentStep()).toBe(5);
    expect(component.errorMessage()).toBeNull();
  });

  it('should display all entered values and photo thumbnails in the review step', () => {
    component.selectCategory('stagnant_water');
    component.state.set('Telangana');
    component.district.set('Rangareddy');
    component.municipality.set('Badangpet');
    component.locality.set('Almasguda Main Road');
    component.latitude.set(17.3142);
    component.longitude.set(78.5284);
    component.duration.set('1-2 weeks');
    component.description.set('Large puddle on roadside with heavy mosquito breeding.');

    const f1 = new File(['mock1'], 'puddle1.jpg', { type: 'image/jpeg' });
    const f2 = new File(['mock2'], 'puddle2.png', { type: 'image/png' });
    component.selectedPhotos.set([f1, f2]);
    component.photoPreviews.set(['data:image/jpeg;base64,mock1', 'data:image/png;base64,mock2']);

    component.currentStep.set(4);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Stagnant Water / Mosquito Breeding Site');
    expect(compiled.textContent).toContain('Telangana');
    expect(compiled.textContent).toContain('Rangareddy');
    expect(compiled.textContent).toContain('Badangpet');
    expect(compiled.textContent).toContain('Almasguda Main Road');
    expect(compiled.textContent).toContain('17.31420');
    expect(compiled.textContent).toContain('1-2 weeks');
    expect(compiled.textContent).toContain('Large puddle on roadside with heavy mosquito breeding.');
    expect(compiled.textContent).toContain('2 of 5 photos attached');

    const thumbs = compiled.querySelectorAll('.review-thumb-img');
    expect(thumbs.length).toBe(2);
  });

  it('should allow removing an individual photo from multi-photo attachments', () => {
    const f1 = new File(['mock1'], 'photo1.jpg', { type: 'image/jpeg' });
    const f2 = new File(['mock2'], 'photo2.jpg', { type: 'image/jpeg' });
    component.selectedPhotos.set([f1, f2]);
    component.photoPreviews.set(['preview1', 'preview2']);

    expect(component.selectedPhotos().length).toBe(2);

    component.removePhoto(0);

    expect(component.selectedPhotos().length).toBe(1);
    expect(component.selectedPhotos()[0].name).toBe('photo2.jpg');
    expect(component.photoPreviews().length).toBe(1);
  });

  it('should reject adding more than 5 photos', () => {
    const photos: File[] = [];
    for (let i = 0; i < 5; i++) {
      photos.push(new File([`data${i}`], `photo${i}.jpg`, { type: 'image/jpeg' }));
    }
    component.selectedPhotos.set(photos);

    // Try adding a 6th photo
    const sixth = new File(['data6'], 'photo6.jpg', { type: 'image/jpeg' });
    (component as any).addPhotos([sixth]);

    expect(component.errorMessage()).toContain('at most 5 photos');
    expect(component.selectedPhotos().length).toBe(5);
  });
});
