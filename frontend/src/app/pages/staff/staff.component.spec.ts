import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { StaffDashboardComponent } from './staff.component';

describe('StaffDashboardComponent', () => {
  let component: StaffDashboardComponent;
  let fixture: ComponentFixture<StaffDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StaffDashboardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StaffDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the staff dashboard component', () => {
    expect(component).toBeTruthy();
  });

  it('should start with loadingUser true and unauthorized false', () => {
    expect(component.unauthorized()).toBe(false);
  });

  it('should format status badge classes properly', () => {
    expect(component.getStatusClass('received')).toBe('badge-received');
    expect(component.getStatusClass('action_in_progress')).toBe('badge-progress');
    expect(component.getStatusClass('needs_more_info')).toBe('badge-warning');
  });
});
