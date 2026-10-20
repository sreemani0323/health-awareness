import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { StaffStatusComponent } from './staff-status.component';
import { CreatorApiService } from '../../../services/creator-api.service';
import { PublicStaffApplicationView } from '../../../models/creator.models';

describe('StaffStatusComponent', () => {
  let component: StaffStatusComponent;
  let fixture: ComponentFixture<StaffStatusComponent>;
  let creatorApi: CreatorApiService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StaffStatusComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StaffStatusComponent);
    component = fixture.componentInstance;
    creatorApi = TestBed.inject(CreatorApiService);
    fixture.detectChanges();
  });

  it('should create the staff status component', () => {
    expect(component).toBeTruthy();
  });

  it('should require reference ID and tracking token to search', () => {
    component.referenceId.set('');
    component.trackingToken.set('');

    component.trackApplication();

    expect(component.errorMessage()).toContain('Both Reference ID and Tracking Token are required');
  });

  it('should load and render application data on valid credentials', () => {
    const mockApp: PublicStaffApplicationView = {
      reference_id: 'APP-2026-X1Y2Z3',
      applicant_name: 'Dr. Suresh Kumar',
      applicant_email: 'suresh@medical.org',
      requested_role: 'reviewer',
      status: 'under_review',
      statement_of_purpose: 'Senior pediatrician with 10 years experience reviewing community health content.',
    };

    vi.spyOn(creatorApi, 'trackStaffApplication').mockReturnValue(of(mockApp));

    component.referenceId.set('APP-2026-X1Y2Z3');
    component.trackingToken.set('sec_app_valid_token');

    component.trackApplication();

    expect(component.application()).toEqual(mockApp);
    expect(component.errorMessage()).toBeNull();
  });

  it('should submit follow-up response when more info is requested', () => {
    const mockApp: PublicStaffApplicationView = {
      reference_id: 'APP-2026-X1Y2Z3',
      applicant_name: 'Dr. Suresh Kumar',
      applicant_email: 'suresh@medical.org',
      requested_role: 'reviewer',
      status: 'more_info_requested',
      statement_of_purpose: 'Statement text',
      info_request_details: 'Please provide registration number.',
    };
    component.application.set(mockApp);
    component.trackingToken.set('sec_app_valid_token');
    component.responseNotes.set('Council registration: APMC/123456');

    vi.spyOn(creatorApi, 'respondToStaffApplication').mockReturnValue(
      of({ reference_id: 'APP-2026-X1Y2Z3', status: 'under_review', message: 'Follow-up received' }),
    );
    const trackSpy = vi.spyOn(component, 'trackApplication');

    component.submitResponse();

    expect(component.successMessage()).toContain('Follow-up information submitted successfully');
    expect(trackSpy).toHaveBeenCalled();
  });

  it('should confirm withdrawal and update status', () => {
    const mockApp: PublicStaffApplicationView = {
      reference_id: 'APP-2026-X1Y2Z3',
      applicant_name: 'Dr. Suresh Kumar',
      applicant_email: 'suresh@medical.org',
      requested_role: 'reviewer',
      status: 'under_review',
      statement_of_purpose: 'Statement text',
    };
    component.application.set(mockApp);
    component.trackingToken.set('sec_app_valid_token');
    component.withdrawRationale.set('Withdrawing due to time constraints.');

    vi.spyOn(creatorApi, 'withdrawStaffApplication').mockReturnValue(
      of({ reference_id: 'APP-2026-X1Y2Z3', status: 'withdrawn', message: 'Withdrawn' }),
    );
    const trackSpy = vi.spyOn(component, 'trackApplication');

    component.confirmWithdraw();

    expect(component.successMessage()).toContain('voluntarily withdrawn');
    expect(component.showWithdrawModal()).toBe(false);
    expect(trackSpy).toHaveBeenCalled();
  });
});
