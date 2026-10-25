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

  describe('OTP and Authentication API flows', () => {
    let fetchSpy: any;

    beforeEach(() => {
      fetchSpy = vi.spyOn(globalThis, 'fetch');
    });

    afterEach(() => {
      fetchSpy.mockRestore();
    });

    it('should initiate registration with requires_otp challenge', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            requires_otp: true,
            challenge_id: 'ch_test123',
            message: 'Verification code sent to test@example.com',
          },
        }),
      } as Response);

      const res = await service.register('Test User', 'test@example.com', 'password123');
      expect(res.success).toBe(true);
      expect(res.requires_otp).toBe(true);
      expect(res.message).toContain('Verification code sent');
      expect(service.isAuthenticated()).toBe(false);
    });

    it('should verify OTP and authenticate learner session', async () => {
      const fakePayload = btoa(
        JSON.stringify({
          sub: 'usr_verified',
          name: 'Verified Learner',
          email: 'test@example.com',
          exp: Math.floor(Date.now() / 1000) + 3600,
        })
      );
      const fakeToken = `h.${fakePayload}.s`;

      fetchSpy.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            token: fakeToken,
            user: { id: 'usr_verified', name: 'Verified Learner', email: 'test@example.com' },
          },
        }),
      } as Response);

      const res = await service.verifySignup('test@example.com', '123456');
      expect(res.success).toBe(true);
      expect(res.token).toBe(fakeToken);
      expect(service.isAuthenticated()).toBe(true);
      expect(service.currentUser()?.email).toBe('test@example.com');
    });

    it('should handle resend OTP successfully', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            message: 'A new verification code has been sent.',
          },
        }),
      } as Response);

      const res = await service.resendOtp('test@example.com', 'signup');
      expect(res.success).toBe(true);
      expect(res.message).toContain('A new verification code');
    });

    it('should initiate password recovery challenge', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            requires_otp: true,
            message: 'If an account exists, a verification code has been sent.',
          },
        }),
      } as Response);

      const res = await service.recover('test@example.com');
      expect(res.success).toBe(true);
      expect(res.requires_otp).toBe(true);
    });

    it('should complete password reset with verified OTP', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            message: 'Password reset successfully.',
          },
        }),
      } as Response);

      const res = await service.resetPassword('test@example.com', '654321', 'newSecurePassword123');
      expect(res.success).toBe(true);
      expect(res.message).toContain('Password reset successfully');
    });
  });
});
