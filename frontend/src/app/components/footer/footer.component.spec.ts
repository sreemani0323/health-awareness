import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { FooterComponent } from './footer.component';

describe('FooterComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FooterComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
  });

  it('should create the footer', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should display the medical advice disclaimer and current year', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.oppia-footer-disclaimer')?.textContent).toContain(
      'not medical advice'
    );
    expect(compiled.textContent).toContain(
      new Date().getFullYear().toString()
    );
  });

  it('should render mission statement and link columns', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.oppia-mission')?.textContent).toContain(
      'evidence-based health education'
    );
    const headings = compiled.querySelectorAll('.oppia-footer-heading');
    expect(headings.length).toBe(3); // ABOUT, LEARN & HELP, FOLLOW US
    expect(headings[0].textContent).toContain('ABOUT');
    expect(headings[1].textContent).toContain('LEARN & HELP');
    expect(headings[2].textContent).toContain('FOLLOW US');
  });

  it('should render the mandatory social media icon row with all 6 channels', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#footer-social-youtube')).toBeTruthy();
    expect(compiled.querySelector('#footer-social-facebook')).toBeTruthy();
    expect(compiled.querySelector('#footer-social-instagram')).toBeTruthy();
    expect(compiled.querySelector('#footer-social-twitter')).toBeTruthy();
    expect(compiled.querySelector('#footer-social-github')).toBeTruthy();
    expect(compiled.querySelector('#footer-social-linkedin')).toBeTruthy();
  });

  it('should render the Google Play promotional badge', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const playBtn = compiled.querySelector('#footer-google-play-btn');
    expect(playBtn).toBeTruthy();
    const playImg = playBtn?.querySelector('img');
    expect(playImg?.getAttribute('src')).toContain('android-landing-google-play.svg');
  });

  it('should render Terms of Service and Privacy Policy links', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#footer-terms-link')?.textContent).toContain('Terms of Service');
    expect(compiled.querySelector('#footer-privacy-link')?.textContent).toContain('Privacy Policy');
  });

  it('should show Coming Soon toast when clicking social or planned links', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.onComingSoonClick('HealthAware official social media');
    fixture.detectChanges();

    expect(component.comingSoonMessage()).toBe('HealthAware official social media');
    const toast = fixture.nativeElement.querySelector('.coming-soon-toast');
    expect(toast).toBeTruthy();
    expect(toast?.textContent).toContain('HealthAware official social media');
    expect(toast?.textContent).toContain('Coming Soon');
  });

  it('should open the Android distribution modal when clicking the Google Play badge', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    const component = fixture.componentInstance;
    const openModalSpy = vi.spyOn(component.distribution, 'openModal');
    fixture.detectChanges();

    const playBtn = fixture.nativeElement.querySelector('#footer-google-play-btn');
    playBtn.click();

    expect(openModalSpy).toHaveBeenCalled();
  });

  it('should render the footer when isNative is false (web platform)', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    const component = fixture.componentInstance;
    vi.spyOn(component, 'isNative', 'get').mockReturnValue(false);
    fixture.detectChanges();

    const footer = fixture.nativeElement.querySelector('#site-footer');
    expect(footer).toBeTruthy();
  });

  it('should suppress the footer when isNative is true (native Capacitor Android app)', () => {
    const fixture = TestBed.createComponent(FooterComponent);
    const component = fixture.componentInstance;
    vi.spyOn(component, 'isNative', 'get').mockReturnValue(true);
    fixture.detectChanges();

    const footer = fixture.nativeElement.querySelector('#site-footer');
    expect(footer).toBeNull();
  });
});
