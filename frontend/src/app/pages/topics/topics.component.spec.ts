import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { TopicsComponent } from './topics.component';
import { ApiService } from '../../services/api.service';
import { Topic } from '../../models/api.models';

describe('TopicsComponent', () => {
  const mockTopics: Topic[] = [
    {
      id: 'topic-hygiene',
      title: 'Personal Hygiene & Handwashing',
      slug: 'hygiene',
      description: 'Hand hygiene and infection prevention',
      display_order: 1,
      cover_image_ref: null,
      cover_image_alt: null,
    },
    {
      id: 'topic-water',
      title: 'Safe Drinking Water & Sanitation',
      slug: 'water',
      description: 'Water purification and storage',
      display_order: 2,
      cover_image_ref: null,
      cover_image_alt: null,
    },
  ];

  let mockApiService: {
    getTopics: ReturnType<typeof vi.fn>;
    getTopicLessons: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    mockApiService = {
      getTopics: vi.fn().mockReturnValue(of(mockTopics)),
      getTopicLessons: vi.fn().mockImplementation((topicId: string) => {
        if (topicId === 'topic-water') {
          return of([{ id: 'l1' }, { id: 'l2' }, { id: 'l3' }]);
        }
        return of([{ id: 'l1' }]);
      }),
    };

    await TestBed.configureTestingModule({
      imports: [TopicsComponent],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: mockApiService },
      ],
    }).compileComponents();
  });

  it('should create the topics component', () => {
    const fixture = TestBed.createComponent(TopicsComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should load and render genuine topics in Oppia topic-card format', () => {
    const fixture = TestBed.createComponent(TopicsComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.topics().length).toBe(2);
    expect(component.loading()).toBe(false);

    const compiled = fixture.nativeElement as HTMLElement;
    const cards = compiled.querySelectorAll('.topic-card');
    expect(cards.length).toBe(2);
    expect(cards[0].textContent).toContain('Personal Hygiene & Handwashing');
    expect(cards[1].textContent).toContain('Safe Drinking Water & Sanitation');
  });

  it('should show error state when API fails', () => {
    mockApiService.getTopics.mockReturnValue(throwError(() => new Error('Network error')));
    const fixture = TestBed.createComponent(TopicsComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    expect(component.loading()).toBe(false);
    expect(component.error()).toContain('Unable to load health topics');

    const compiled = fixture.nativeElement as HTMLElement;
    const errorAlert = compiled.querySelector('.error-state');
    expect(errorAlert).toBeTruthy();
    expect(errorAlert?.textContent).toContain('Unable to load health topics');
  });

  it('should render breadcrumbs linking back to home', () => {
    const fixture = TestBed.createComponent(TopicsComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const homeBreadcrumb = compiled.querySelector('#breadcrumb-home');
    expect(homeBreadcrumb).toBeTruthy();
    expect(homeBreadcrumb?.textContent).toContain('Home');
  });

  it('should render custom SVG icons for topics instead of emojis', () => {
    const fixture = TestBed.createComponent(TopicsComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const svgIcons = compiled.querySelectorAll('.topic-svg-icon');
    expect(svgIcons.length).toBe(2);
    expect(compiled.querySelector('.topic-thumbnail-emoji')).toBeNull();
  });

  it('should dynamically calculate and render chapter counts per topic', () => {
    const fixture = TestBed.createComponent(TopicsComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const lessonCountBadges = compiled.querySelectorAll('.topic-lesson-count');
    expect(lessonCountBadges.length).toBe(2);
    expect(lessonCountBadges[0].textContent).toContain('1 Complete Chapter');
    expect(lessonCountBadges[1].textContent).toContain('3 Complete Chapters');
  });
});
