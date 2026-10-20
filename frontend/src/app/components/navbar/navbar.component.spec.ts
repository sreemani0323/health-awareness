import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NavbarComponent } from './navbar.component';
import { ComingSoonService } from '../../services/coming-soon.service';

describe('NavbarComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavbarComponent],
      providers: [provideRouter([]), ComingSoonService],
    }).compileComponents();
  });

  it('should create the navbar', () => {
    const fixture = TestBed.createComponent(NavbarComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should render brand title and Oppia navigation items', () => {
    const fixture = TestBed.createComponent(NavbarComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.oppia-brand-text')?.textContent).toContain('HealthAware');
    expect(compiled.querySelector('#nav-home')?.textContent?.trim()).toBe('Home');
    expect(compiled.querySelector('#nav-learn')?.textContent?.trim()).toBe('Learn');
    expect(compiled.querySelector('#nav-about')?.textContent?.trim()).toBe('About');
    expect(compiled.querySelector('#nav-get-involved')?.textContent?.trim()).toBe('Get Involved');
  });

  it('should toggle mobile menu on mobile toggle click', () => {
    const fixture = TestBed.createComponent(NavbarComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.isMobileMenuOpen()).toBe(false);
    component.toggleMobileMenu();
    expect(component.isMobileMenuOpen()).toBe(true);
    component.closeMobileMenu();
    expect(component.isMobileMenuOpen()).toBe(false);
  });

  it('should render learner sync progress button when anonymous', () => {
    const fixture = TestBed.createComponent(NavbarComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const syncBtn = compiled.querySelector('#nav-learner-save-progress');
    expect(syncBtn).toBeTruthy();
    expect(syncBtn?.textContent).toContain('Sync Progress');
  });
});
