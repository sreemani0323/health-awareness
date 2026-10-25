import { TestBed } from '@angular/core/testing';
import { of, throwError, firstValueFrom } from 'rxjs';
import { BackendWarmupService } from './backend-warmup.service';
import { ApiService } from './api.service';

describe('BackendWarmupService', () => {
  let service: BackendWarmupService;
  let apiSpy: {
    getReadiness: ReturnType<typeof vi.fn>;
    getTopics: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    apiSpy = {
      getReadiness: vi.fn(),
      getTopics: vi.fn().mockReturnValue(of([])),
    };

    TestBed.configureTestingModule({
      providers: [
        BackendWarmupService,
        { provide: ApiService, useValue: apiSpy },
      ],
    });

    service = TestBed.inject(BackendWarmupService);
  });

  it('should be created with initial idle state', () => {
    expect(service).toBeTruthy();
    expect(service.isReady()).toBe(false);
    expect(service.isWarming()).toBe(false);
    expect(service.warmupError()).toBeNull();
  });

  it('should mark backend ready and prefetch curriculum on healthy readiness response', async () => {
    apiSpy.getReadiness.mockReturnValue(of({ status: 'ready', database: 'connected' }));

    const result = await firstValueFrom(service.warmup());
    expect(result.ready).toBe(true);
    expect(result.database).toBe('connected');
    expect(service.isReady()).toBe(true);
    expect(service.isWarming()).toBe(false);
    expect(service.warmupError()).toBeNull();
    expect(apiSpy.getTopics).toHaveBeenCalled();
  });

  it('should handle slow, sleeping, or failing backend gracefully without crashing', async () => {
    apiSpy.getReadiness.mockReturnValue(throwError(() => new Error('Connection refused')));

    const result = await firstValueFrom(service.warmup());
    expect(result.ready).toBe(false);
    expect(result.database).toBe('disconnected');
    expect(service.isReady()).toBe(false);
    expect(service.isWarming()).toBe(false);
    expect(service.warmupError()).toContain('Connection refused');
  });

  it('should deduplicate simultaneous warmup requests', () => {
    apiSpy.getReadiness.mockReturnValue(of({ status: 'ready', database: 'connected' }));

    const sub1 = service.warmup();
    const sub2 = service.warmup();

    expect(sub1).toBe(sub2);
    expect(apiSpy.getReadiness).toHaveBeenCalledTimes(1);
  });

  it('should allow retrying warmup after degraded state', async () => {
    apiSpy.getReadiness.mockReturnValueOnce(throwError(() => new Error('Timeout')));

    await firstValueFrom(service.warmup());
    expect(service.isReady()).toBe(false);

    // Now backend wakes up
    apiSpy.getReadiness.mockReturnValueOnce(of({ status: 'ready', database: 'connected' }));
    const retryRes = await firstValueFrom(service.retry());
    expect(retryRes.ready).toBe(true);
    expect(service.isReady()).toBe(true);
  });
});
