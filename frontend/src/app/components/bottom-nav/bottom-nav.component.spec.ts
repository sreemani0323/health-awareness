import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { BottomNavComponent } from './bottom-nav.component';
import { LearningProgressService } from '../../services/learning-progress.service';

describe('BottomNavComponent', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [BottomNavComponent],
      providers: [provideRouter([]), LearningProgressService],
    }).compileComponents();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should create the bottom nav component', () => {
    const fixture = TestBed.createComponent(BottomNavComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should render all 4 core navigation destinations', () => {
    const fixture = TestBed.createComponent(BottomNavComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#bottom-nav-home')).toBeTruthy();
    expect(compiled.querySelector('#bottom-nav-topics')).toBeTruthy();
    expect(compiled.querySelector('#bottom-nav-report')).toBeTruthy();
    expect(compiled.querySelector('#bottom-nav-track')).toBeTruthy();
  });

  it('should display completed lessons count badge when progress exists', () => {
    const progressService = TestBed.inject(LearningProgressService);
    progressService.markLessonCompleted('lesson-handwashing', 'topic-hygiene');

    const fixture = TestBed.createComponent(BottomNavComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const badge = compiled.querySelector('.nav-badge');
    expect(badge).toBeTruthy();
    expect(badge?.textContent).toContain('1');
  });
});
