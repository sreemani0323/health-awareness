import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { StaffApplyComponent } from './staff-apply.component';
import { CreatorApiService } from '../../../services/creator-api.service';

describe('StaffApplyComponent', () => {
  let component: StaffApplyComponent;
  let fixture: ComponentFixture<StaffApplyComponent>;
  let creatorApi: CreatorApiService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StaffApplyComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StaffApplyComponent);
    component = fixture.componentInstance;
    creatorApi = TestBed.inject(CreatorApiService);
    fixture.detectChanges();
  });

  it('should create the staff application component', () => {
    expect(component).toBeTruthy();
    expect(component.requestedRole()).toBe('contributor');
  });

  it('should validate statement of purpose length before submitting', () => {
    component.applicantName.set('Test Doctor');
    component.applicantEmail.set('doctor@clinic.org');
    component.statementOfPurpose.set('Too short');
    component.evidenceStandardsAcknowledged.set(true);
    component.childSafetyAcknowledged.set(true);

    component.submitApplication();

    expect(component.errorMessage()).toContain('at least 30 characters');
    expect(component.submitting()).toBe(false);
  });

  it('should validate required declarations before submitting', () => {
    component.applicantName.set('Test Doctor');
    component.applicantEmail.set('doctor@clinic.org');
    component.statementOfPurpose.set('This is a sufficiently long statement of purpose explaining my pediatric experience.');
    component.evidenceStandardsAcknowledged.set(false);
    component.childSafetyAcknowledged.set(true);

    component.submitApplication();

    expect(component.errorMessage()).toContain('evidence-based health standards');
  });

  it('should submit valid application and render credentials result', () => {
    const mockResponse = {
      reference_id: 'APP-2026-TEST01',
      tracking_token: 'sec_app_sample_token_123',
      status: 'pending_review',
      message: 'Application registered successfully.',
    };
    vi.spyOn(creatorApi, 'submitStaffApplication').mockReturnValue(of(mockResponse));

    component.applicantName.set('Dr. Radha Rao');
    component.applicantEmail.set('radha.rao@guntur.org');
    component.statementOfPurpose.set('I am a senior clinical specialist wishing to contribute peer reviews.');
    component.evidenceStandardsAcknowledged.set(true);
    component.childSafetyAcknowledged.set(true);

    component.submitApplication();

    expect(component.submissionResult()).toEqual(mockResponse);
    expect(component.errorMessage()).toBeNull();
  });

  it('should handle submission conflict error gracefully', () => {
    vi.spyOn(creatorApi, 'submitStaffApplication').mockReturnValue(
      throwError(() => ({
        error: {
          error: {
            message: 'An active application with this email address is already under review.',
          },
        },
      })),
    );

    component.applicantName.set('Dr. Radha Rao');
    component.applicantEmail.set('radha.rao@guntur.org');
    component.statementOfPurpose.set('I am a senior clinical specialist wishing to contribute peer reviews.');
    component.evidenceStandardsAcknowledged.set(true);
    component.childSafetyAcknowledged.set(true);

    component.submitApplication();

    expect(component.errorMessage()).toContain('already under review');
  });
});
