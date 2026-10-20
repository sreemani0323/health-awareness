import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { AboutComponent } from './about.component';

describe('AboutComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AboutComponent],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create the about component', () => {
    const fixture = TestBed.createComponent(AboutComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should render mission, standards, and action buttons', () => {
    const fixture = TestBed.createComponent(AboutComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#about-page')).toBeTruthy();
    expect(compiled.querySelector('.hero-title')?.textContent).toContain('About HealthAware');
    expect(compiled.querySelector('#about-topics-link')).toBeTruthy();
    expect(compiled.querySelector('#about-report-link')).toBeTruthy();
    expect(compiled.querySelector('#about-get-involved-btn')).toBeTruthy();
    expect(compiled.querySelector('#about-apply-btn')).toBeTruthy();
  });
});
