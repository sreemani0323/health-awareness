import { TestBed } from '@angular/core/testing';
import { NetworkStatusService } from './network-status.service';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';

describe('NetworkStatusService', () => {
  let service: NetworkStatusService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        NetworkStatusService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(NetworkStatusService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should initialize and provide default online state', () => {
    expect(service).toBeTruthy();
    expect(typeof service.isOnline()).toBe('boolean');
    expect(service.connectionStatus()).toBe('online');
  });

  it('handles offline event by transitioning connectionStatus to offline', () => {
    service.handleOfflineEvent();
    expect(service.isOnline()).toBe(false);
    expect(service.connectionStatus()).toBe('offline');
  });

  it('handles online event and triggers reachability probe', async () => {
    service.handleOfflineEvent();
    expect(service.isOnline()).toBe(false);

    let reconnectCalled = false;
    service.onReconnect(() => {
      reconnectCalled = true;
    });

    const onlinePromise = service.handleOnlineEvent();

    // Verify /api/v1/health probe is sent
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/health`);
    expect(req.request.method).toBe('GET');
    req.flush({ data: { status: 'healthy' } });

    await onlinePromise;

    expect(service.isOnline()).toBe(true);
    expect(service.isDegraded()).toBe(false);
    expect(service.connectionStatus()).toBe('online');
    expect(reconnectCalled).toBe(true);
  });

  it('marks service degraded if online probe fails', async () => {
    const reachabilityPromise = service.checkReachability();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/health`);
    req.flush('Service unavailable', { status: 503, statusText: 'Service Unavailable' });

    const reachable = await reachabilityPromise;

    expect(reachable).toBe(false);
    expect(service.isDegraded()).toBe(true);
    expect(service.connectionStatus()).toBe('degraded');
  });

  it('tracks pending sync count and formats appropriately', () => {
    expect(service.pendingSyncCount()).toBe(0);
    service.setPendingSyncCount(3);
    expect(service.pendingSyncCount()).toBe(3);
    service.setPendingSyncCount(-1);
    expect(service.pendingSyncCount()).toBe(0);
  });
});
