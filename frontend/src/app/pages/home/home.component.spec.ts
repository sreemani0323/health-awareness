import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { HomeComponent } from './home.component';
import { ComingSoonService } from '../../services/coming-soon.service';
import { LearningProgressService, PRACTICAL_ACTIVITIES } from '../../services/learning-progress.service';

describe('HomeComponent', () => {
  let comingSoonService: ComingSoonService;
  let progressService: LearningProgressService;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [HomeComponent],
      providers: [provideRouter([]), ComingSoonService, LearningProgressService],
    }).compileComponents();

    comingSoonService = TestBed.inject(ComingSoonService);
    progressService = TestBed.inject(LearningProgressService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should create the home component', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should render the Oppia hero section with child-learning photograph and starting actions', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const hero = compiled.querySelector('#hero-section');
    expect(hero).toBeTruthy();
    expect(compiled.querySelector('.oppia-splash-h1')?.textContent).toContain(
      'Everyday Health Knowledge for Everyone'
    );
    expect(compiled.querySelector('#hero-explore-btn')?.textContent).toContain(
      'Explore Health Topics'
    );
    expect(compiled.querySelector('#hero-activity-btn')?.textContent).toContain(
      'Try a Small Health Activity'
    );
    expect(compiled.querySelector('#hero-android-btn')?.textContent).toContain(
      'Access the Android App'
    );

    // Continue learning should NOT be present when no saved progress exists
    expect(compiled.querySelector('#hero-continue-learning-btn')).toBeNull();

    const childPhoto = compiled.querySelector('.splash-main-img-desktop');
    expect(childPhoto).toBeTruthy();
    expect(childPhoto?.getAttribute('src')).toContain('main_photo.jpg');
  });

  it('should render Resume Lesson in hero when valid progress exists', () => {
    progressService.saveLessonProgress(
      'lesson-handwashing',
      'Effective Handwashing Techniques',
      'topic-hygiene',
      1,
      3
    );

    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const continueBtn = compiled.querySelector('#hero-continue-learning-btn');
    expect(continueBtn).toBeTruthy();
    expect(continueBtn?.textContent).toContain('Resume Lesson');
    expect(compiled.querySelector('.resume-title')?.textContent).toContain(
      'Effective Handwashing Techniques'
    );
    expect(compiled.querySelector('.resume-step')?.textContent).toContain('Card 2 of 3 (67%)');
    expect(compiled.querySelector('.resume-badge--in-progress')?.textContent).toContain('In Progress');
  });

  it('should render Review Lesson in hero when lesson has been completed', () => {
    progressService.saveLessonProgress(
      'lesson-handwashing',
      'Effective Handwashing Techniques',
      'topic-hygiene',
      2,
      3
    );
    progressService.markLessonCompleted('lesson-handwashing', 'topic-hygiene');

    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const continueBtn = compiled.querySelector('#hero-continue-learning-btn');
    expect(continueBtn).toBeTruthy();
    expect(continueBtn?.textContent).toContain('Review Lesson');
    expect(compiled.querySelector('.resume-badge--completed')?.textContent).toContain('Completed Lesson');
  });

  it('should require confirmation before clearing active lesson bookmark and cancel preserves it', () => {
    progressService.saveLessonProgress(
      'lesson-handwashing',
      'Effective Handwashing Techniques',
      'topic-hygiene',
      1,
      3
    );

    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const clearBtn = compiled.querySelector('#hero-clear-resume-btn') as HTMLButtonElement;
    expect(clearBtn).toBeTruthy();
    expect(clearBtn.textContent).toContain('Clear saved progress');

    // Click clear triggers confirmation dialog
    clearBtn.click();
    fixture.detectChanges();

    const modal = compiled.querySelector('.clear-confirm-modal');
    expect(modal).toBeTruthy();
    expect(compiled.querySelector('#clear-dialog-title')?.textContent).toContain('Clear Saved Lesson Bookmark?');

    // Cancel leaves progress intact
    const cancelBtn = compiled.querySelector('#btn-cancel-clear-progress') as HTMLButtonElement;
    cancelBtn.click();
    fixture.detectChanges();

    expect(progressService.hasResume()).toBe(true);
    expect(compiled.querySelector('.clear-confirm-modal')).toBeNull();

    // Confirm clears bookmark
    clearBtn.click();
    fixture.detectChanges();
    const confirmBtn = compiled.querySelector('#btn-confirm-clear-progress') as HTMLButtonElement;
    confirmBtn.click();
    fixture.detectChanges();

    expect(progressService.hasResume()).toBe(false);
  });

  it('should render featured lesson and practical health tip', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const featuredSection = compiled.querySelector('.featured-tip-section');
    expect(featuredSection).toBeTruthy();
    expect(compiled.querySelector('#featured-lesson-heading')?.textContent).toContain(
      'Effective Handwashing Techniques'
    );
    expect(compiled.querySelector('#start-featured-lesson-btn')).toBeTruthy();
    expect(compiled.querySelector('.tip-title')?.textContent).toContain(
      'Lather Friction Removes Microbes'
    );
    expect(compiled.querySelector('#home-family-challenge-btn')).toBeTruthy();
  });

  it('should render “Try This at Home” practical activities and toggle completion', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const activitiesSection = compiled.querySelector('#family-activities');
    expect(activitiesSection).toBeTruthy();
    expect(compiled.querySelectorAll('.activity-card').length).toBe(PRACTICAL_ACTIVITIES.length);

    const firstToggle = compiled.querySelector('#toggle-' + PRACTICAL_ACTIVITIES[0].id) as HTMLButtonElement;
    expect(firstToggle).toBeTruthy();
    expect(firstToggle.textContent).toContain('Mark as Practiced');

    firstToggle.click();
    fixture.detectChanges();

    expect(progressService.isActivityCompleted(PRACTICAL_ACTIVITIES[0].id)).toBe(true);
    expect(firstToggle.textContent).toContain('Completed Today');
  });

  it('should render saved milestones and allow clearing device progress with confirmation', () => {
    progressService.saveLessonProgress('lesson-handwashing', 'Handwashing', 'topic-hygiene', 2, 3);
    progressService.markLessonCompleted('lesson-handwashing', 'topic-hygiene');

    const fixture = TestBed.createComponent(HomeComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('.device-progress-section')).toBeTruthy();
    expect(compiled.querySelector('.stat-number')?.textContent).toContain('1');

    const clearBtn = compiled.querySelector('#clear-all-device-progress-btn') as HTMLButtonElement;
    expect(clearBtn).toBeTruthy();

    clearBtn.click();
    fixture.detectChanges();

    // Confirmation dialog appears
    const confirmBtn = compiled.querySelector('#btn-confirm-clear-progress') as HTMLButtonElement;
    expect(confirmBtn).toBeTruthy();
    confirmBtn.click();
    fixture.detectChanges();

    expect(progressService.hasResume()).toBe(false);
    expect(progressService.completedCount()).toBe(0);
  });

  it('should render the Oppia highlights strip', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const highlights = compiled.querySelector('.oppia-splash-section-two');
    expect(highlights).toBeTruthy();
    expect(highlights?.textContent).toContain('Practical Health Guidance');
    expect(highlights?.textContent).toContain('Community-Focused Learning');
    expect(highlights?.textContent).toContain('Evidence-Informed Resources');
  });

  it('should render the benefits section with bullet items', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#benefits-heading')?.textContent).toContain(
      'Health Knowledge Made Easier'
    );
    const benefits = compiled.querySelectorAll('.splash-benefits');
    expect(benefits.length).toBe(3);
    expect(benefits[0].textContent).toContain('Simple, understandable explanations');

    const benefitsImg = compiled.querySelector('.splash-matthew-image');
    expect(benefitsImg?.getAttribute('src')).toContain('health-benefits.svg');
  });

  it('should render the communities section with community-care.svg', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const communityImg = compiled.querySelector('.splash-community-image');
    expect(communityImg?.getAttribute('src')).toContain('community-care.svg');
  });

  it('should render the educators section with Coming Soon button', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#educators-section')).toBeTruthy();
    expect(compiled.querySelector('#teachers-heading')?.textContent).toContain(
      'Share Health Knowledge'
    );
    expect(compiled.querySelector('#educator-resources-btn')).toBeTruthy();
  });

  it('should render the newsletter section with subscribe button', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#newsletter-section')).toBeTruthy();
    expect(compiled.querySelector('#newsletter-heading')?.textContent).toContain(
      'Stay Updated'
    );
    expect(compiled.querySelector('#newsletter-subscribe-btn')).toBeTruthy();
  });

  it('should show Coming Soon toast when clicking an educator resources button', () => {
    const fixture = TestBed.createComponent(HomeComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.showComingSoon('Educator resources');
    fixture.detectChanges();

    expect(component.comingSoonMessage()).toBe('Educator resources');
    const toast = fixture.nativeElement.querySelector('.coming-soon-toast');
    expect(toast).toBeTruthy();
    expect(toast?.textContent).toContain('Coming Soon');
  });
});
