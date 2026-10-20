import { TestBed } from '@angular/core/testing';
import { LearnerAuthService } from './learner-auth.service';

describe('LearnerAuthService', () => {
  let service: LearnerAuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(LearnerAuthService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created with initial unauthenticated state', () => {
    expect(service).toBeTruthy();
    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentUser()).toBeNull();
    expect(service.getToken()).toBeNull();
    expect(service.displayName()).toBe('Learner');
  });

  it('should set session and authenticate learner with profile', () => {
    // Basic JWT header.payload.signature structure
    // Payload: {"sub": "usr_test123", "name": "Jane Learner", "email": "jane@example.com", "exp": 9999999999}
    const fakePayload = btoa(
      JSON.stringify({
        sub: 'usr_test123',
        name: 'Jane Learner',
        email: 'jane@example.com',
        exp: Math.floor(Date.now() / 1000) + 3600,
      })
    );
    const fakeToken = `header.${fakePayload}.signature`;

    service.setSession(fakeToken);

    expect(service.isAuthenticated()).toBe(true);
    expect(service.currentUser()?.id).toBe('usr_test123');
    expect(service.currentUser()?.name).toBe('Jane Learner');
    expect(service.displayName()).toBe('Jane Learner');
    expect(service.getToken()).toBe(fakeToken);
  });

  it('should clear session on logout without affecting anonymous learning defaults', () => {
    const fakePayload = btoa(JSON.stringify({ sub: 'usr_1', exp: Math.floor(Date.now() / 1000) + 3600 }));
    service.setSession(`h.${fakePayload}.s`);
    expect(service.isAuthenticated()).toBe(true);

    service.logout();

    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentUser()).toBeNull();
    expect(service.getToken()).toBeNull();
    expect(service.syncStatus()).toBe('idle');
    expect(service.lastSyncedAt()).toBeNull();
    expect(service.errorMessage()).toBeNull();
  });

  it('should proactively detect expired token in getToken() and log out', () => {
    // Expired token (exp in the past)
    const expiredPayload = btoa(
      JSON.stringify({
        sub: 'usr_expired',
        name: 'Expired Learner',
        exp: Math.floor(Date.now() / 1000) - 300,
      })
    );
    const expiredToken = `h.${expiredPayload}.s`;
    localStorage.setItem('healthaware_learner_jwt', expiredToken);
    localStorage.setItem('healthaware_learner_profile', JSON.stringify({ id: 'usr_expired', name: 'Expired' }));

    const token = service.getToken();
    expect(token).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('healthaware_learner_jwt')).toBeNull();
  });
});
