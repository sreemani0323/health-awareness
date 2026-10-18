import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TrackConcernComponent } from './track.component';

describe('TrackConcernComponent', () => {
  let component: TrackConcernComponent;
  let fixture: ComponentFixture<TrackConcernComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TrackConcernComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TrackConcernComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the track concern component', () => {
    expect(component).toBeTruthy();
  });

  it('should validate that both reference ID and tracking token are provided', () => {
    component.referenceId.set('');
    component.trackingToken.set('');
    component.lookupConcern();
    expect(component.errorMessage()).toContain('Both Reference ID and Private Tracking Token are required');
  });

  it('should return appropriate status badge class', () => {
    expect(component.getStatusClass('received')).toBe('badge-received');
    expect(component.getStatusClass('under_review')).toBe('badge-review');
    expect(component.getStatusClass('assigned')).toBe('badge-progress');
    expect(component.getStatusClass('resolved')).toBe('badge-resolved');
    expect(component.getStatusClass('rejected')).toBe('badge-rejected');
  });
});
