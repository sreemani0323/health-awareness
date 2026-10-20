import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { GetInvolvedComponent } from './get-involved.component';

describe('GetInvolvedComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GetInvolvedComponent],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create the get involved component', () => {
    const fixture = TestBed.createComponent(GetInvolvedComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should render all participation cards and functional links', () => {
    const fixture = TestBed.createComponent(GetInvolvedComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#get-involved-page')).toBeTruthy();
    expect(compiled.querySelector('#get-involved-topics-btn')).toBeTruthy();
    expect(compiled.querySelector('#get-involved-report-btn')).toBeTruthy();
    expect(compiled.querySelector('#get-involved-apply-btn')).toBeTruthy();
    expect(compiled.querySelector('#get-involved-creator-btn')).toBeTruthy();

    const applyBtn = compiled.querySelector('#get-involved-apply-btn');
    expect(applyBtn?.getAttribute('routerLink')).toBe('/staff/apply');
  });
});
