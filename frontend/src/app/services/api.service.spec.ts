import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';
import { Topic, LessonSummary, LessonDetail, HealthCheck, ApiResponse } from '../models/api.models';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const baseUrl = environment.apiBaseUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ApiService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get topics unwrapping the envelope data', () => {
    const mockTopics: Topic[] = [
      {
        id: 't-1',
        title: 'Hygiene',
        slug: 'hygiene',
        description: 'Handwashing and sanitization',
        display_order: 1,
        cover_image_ref: null,
        cover_image_alt: null,
      },
    ];
    const mockResponse: ApiResponse<Topic[]> = {
      data: mockTopics,
      meta: { api_version: 'v1' },
    };

    service.getTopics().subscribe((topics) => {
      expect(topics.length).toBe(1);
      expect(topics[0].title).toBe('Hygiene');
    });

    const req = httpMock.expectOne(`${baseUrl}/topics`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should get topic lessons unwrapping data', () => {
    const mockLessons: LessonSummary[] = [
      {
        id: 'l-1',
        topic_id: 't-1',
        title: 'Effective Handwashing',
        summary: 'Proper techniques',
        language: 'en',
        estimated_duration_minutes: 5,
        published_version_id: 'v-1',
        display_order: 1,
      },
    ];
    const mockResponse: ApiResponse<LessonSummary[]> = {
      data: mockLessons,
      meta: { api_version: 'v1' },
    };

    service.getTopicLessons('t-1').subscribe((lessons) => {
      expect(lessons.length).toBe(1);
      expect(lessons[0].id).toBe('l-1');
    });

    const req = httpMock.expectOne(`${baseUrl}/topics/t-1/lessons`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should get lesson detail unwrapping data', () => {
    const mockDetail: LessonDetail = {
      id: 'l-1',
      topic_id: 't-1',
      version_id: 'v-1',
      version_number: 1,
      title: 'Hand Hygiene Steps',
      summary: 'Learn 7-step handwashing',
      language: 'en',
      learning_objectives: ['Master technique'],
      estimated_duration_minutes: 5,
      cards: [],
      sources: [],
    };
    const mockResponse: ApiResponse<LessonDetail> = {
      data: mockDetail,
      meta: { api_version: 'v1' },
    };

    service.getLessonDetail('l-1').subscribe((detail) => {
      expect(detail.title).toBe('Hand Hygiene Steps');
      expect(detail.learning_objectives).toContain('Master technique');
    });

    const req = httpMock.expectOne(`${baseUrl}/lessons/l-1`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should check health unwrapping data', () => {
    const mockHealth: HealthCheck = { status: 'healthy' };
    const mockResponse: ApiResponse<HealthCheck> = {
      data: mockHealth,
      meta: { api_version: 'v1' },
    };

    service.getHealth().subscribe((health) => {
      expect(health.status).toBe('healthy');
    });

    const req = httpMock.expectOne(`${baseUrl}/health`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });
});
