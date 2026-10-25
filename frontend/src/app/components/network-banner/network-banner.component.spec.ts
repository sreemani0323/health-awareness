import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NetworkBannerComponent } from './network-banner.component';
import { NetworkStatusService } from '../../services/network-status.service';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

describe('NetworkBannerComponent', () => {
  let component: NetworkBannerComponent;
  let fixture: ComponentFixture<NetworkBannerComponent>;
  let networkService: NetworkStatusService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NetworkBannerComponent],
      providers: [
        NetworkStatusService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NetworkBannerComponent);
    component = fixture.componentInstance;
    networkService = TestBed.inject(NetworkStatusService);
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('does not display banner when online and healthy', () => {
    const banner = fixture.nativeElement.querySelector('.network-banner');
    expect(banner).toBeNull();
  });

  it('displays offline banner with calm, accessible message when offline', () => {
    networkService.handleOfflineEvent();
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.network-banner');
    expect(banner).toBeTruthy();
    expect(banner.classList.contains('network-banner--offline')).toBe(true);
    expect(banner.textContent).toContain("You're reading offline");
    expect(banner.textContent).toContain('progress is saved locally');
  });

  it('displays queued updates badge when offline progress is pending sync', () => {
    networkService.handleOfflineEvent();
    networkService.setPendingSyncCount(2);
    fixture.detectChanges();

    const badge = fixture.nativeElement.querySelector('.pending-sync-badge');
    expect(badge).toBeTruthy();
    expect(badge.textContent).toContain('2 progress updates queued');
  });

  it('displays degraded service message when service is degraded', () => {
    networkService.setDegraded(true);
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.network-banner');
    expect(banner).toBeTruthy();
    expect(banner.classList.contains('network-banner--degraded')).toBe(true);
    expect(banner.textContent).toContain('Service connection is limited');
  });

  it('allows dismissing the banner', () => {
    networkService.handleOfflineEvent();
    fixture.detectChanges();

    component.dismiss();
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.network-banner');
    expect(banner).toBeNull();
  });
});
