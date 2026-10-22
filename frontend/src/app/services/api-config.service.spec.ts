import { TestBed } from '@angular/core/testing';
import { ApiConfigService } from './api-config.service';

describe('ApiConfigService', () => {
  let service: ApiConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ApiConfigService],
    });
    service = TestBed.inject(ApiConfigService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should return relative /api/v1 in web browser environment', () => {
    // In node/browser test runner, Capacitor is not on native platform
    expect(service.isNative).toBe(false);
    expect(service.apiBaseUrl).toBe('/api/v1');
  });

  it('should correctly format relative endpoint URLs', () => {
    expect(service.getApiUrl('/topics')).toBe('/api/v1/topics');
    expect(service.getApiUrl('topics')).toBe('/api/v1/topics');
    expect(service.getApiUrl('auth/login')).toBe('/api/v1/auth/login');
  });
});
