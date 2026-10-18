import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { ReportConcernComponent } from './report.component';

describe('ReportConcernComponent', () => {
  let component: ReportConcernComponent;
  let fixture: ComponentFixture<ReportConcernComponent>;

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
});
