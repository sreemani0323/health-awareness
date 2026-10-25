import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LearnerAuthModalComponent } from './learner-auth-modal.component';
import { LearnerAuthService } from '../../services/learner-auth.service';
import { LearningProgressService } from '../../services/learning-progress.service';

describe('LearnerAuthModalComponent', () => {
  let mockLearnerAuth: Partial<LearnerAuthService>;
  let mockProgressService: Partial<LearningProgressService>;

  beforeEach(async () => {
    mockLearnerAuth = {
      login: vi.fn().mockResolvedValue({ success: true, token: 'mock-jwt', user: { id: 'u1', name: 'Learner One' } }),
      register: vi.fn().mockResolvedValue({ success: true, requires_otp: true, message: 'Verification code sent.' }),
      verifySignup: vi.fn().mockResolvedValue({ success: true, token: 'mock-jwt', user: { id: 'u1', name: 'Learner One' } }),
      resendOtp: vi.fn().mockResolvedValue({ success: true, message: 'New code sent.' }),
      recover: vi.fn().mockResolvedValue({ success: true, message: 'Recovery code sent.' }),
      resetPassword: vi.fn().mockResolvedValue({ success: true, message: 'Password updated successfully!' }),
    };

    mockProgressService = {
      syncWithRemote: vi.fn().mockResolvedValue(undefined),
    };

    await TestBed.configureTestingModule({
      imports: [LearnerAuthModalComponent],
      providers: [
        provideRouter([]),
        { provide: LearnerAuthService, useValue: mockLearnerAuth },
        { provide: LearningProgressService, useValue: mockProgressService },
      ],
    }).compileComponents();
  });

  it('should create the learner auth modal', () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
    expect(component.isOpen()).toBe(false);
  });

  it('should open to login tab and close properly', () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.open('login');
    expect(component.isOpen()).toBe(true);
    expect(component.activeTab()).toBe('login');

    component.close();
    expect(component.isOpen()).toBe(false);
  });

  it('should open to register tab and validate passwords', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.open('register');
    fixture.detectChanges();

    component.displayName = 'Maya Sharma';
    component.email = 'maya@example.com';
    component.password = 'short';
    component.confirmPassword = 'short';

    await component.onRegister();
    expect(component.errorMessage()).toContain('at least 8 characters');

    component.password = 'password123';
    component.confirmPassword = 'mismatch123';
    await component.onRegister();
    expect(component.errorMessage()).toContain('do not match');
  });

  it('should successfully log in and trigger remote sync', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.open('login');
    fixture.detectChanges();

    component.email = 'maya@example.com';
    component.password = 'correctpassword123';

    await component.onLogin();
    expect(mockLearnerAuth.login).toHaveBeenCalledWith('maya@example.com', 'correctpassword123');
    expect(mockProgressService.syncWithRemote).toHaveBeenCalled();
  });

  it('should transition to verify-signup tab when registration requires OTP', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.open('register');
    fixture.detectChanges();

    component.displayName = 'Maya Sharma';
    component.email = 'maya@example.com';
    component.password = 'password123';
    component.confirmPassword = 'password123';

    await component.onRegister();
    expect(mockLearnerAuth.register).toHaveBeenCalledWith('Maya Sharma', 'maya@example.com', 'password123');
    expect(component.activeTab()).toBe('verify-signup');
    expect(component.successMessage()).toContain('Verification code sent');
  });

  it('should validate OTP length and verify signup with 6 digits', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.open('register');
    component.email = 'maya@example.com';
    component.activeTab.set('verify-signup');
    fixture.detectChanges();

    component.otp = '123';
    await component.onVerifySignup();
    expect(component.errorMessage()).toContain('6-digit verification code');
    expect(mockLearnerAuth.verifySignup).not.toHaveBeenCalled();

    component.otp = '123456';
    await component.onVerifySignup();
    expect(mockLearnerAuth.verifySignup).toHaveBeenCalledWith('maya@example.com', '123456');
    expect(mockProgressService.syncWithRemote).toHaveBeenCalled();
    expect(component.successMessage()).toContain('verified and created');
  });

  it('should allow resending OTP for signup', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.email = 'maya@example.com';
    await component.onResendOtp('signup');
    expect(mockLearnerAuth.resendOtp).toHaveBeenCalledWith('maya@example.com', 'signup');
    expect(component.successMessage()).toContain('New code sent.');
  });

  it('should initiate password recovery and transition to reset-password tab', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.open('login');
    component.switchTab('recover');
    fixture.detectChanges();

    component.email = 'learner@example.com';
    await component.onRecover();
    expect(mockLearnerAuth.recover).toHaveBeenCalledWith('learner@example.com');
    expect(component.activeTab()).toBe('reset-password');
  });

  it('should validate password matching and reset password with OTP', async () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    const component = fixture.componentInstance;
    component.email = 'learner@example.com';
    component.activeTab.set('reset-password');
    fixture.detectChanges();

    component.otp = '654321';
    component.newPassword = 'newPassword123';
    component.confirmNewPassword = 'differentPassword';
    await component.onResetPassword();
    expect(component.errorMessage()).toContain('do not match');

    component.confirmNewPassword = 'newPassword123';
    await component.onResetPassword();
    expect(mockLearnerAuth.resetPassword).toHaveBeenCalledWith('learner@example.com', '654321', 'newPassword123');
    expect(component.activeTab()).toBe('login');
    expect(component.successMessage()).toContain('Password updated successfully');
  });

  it('should render institutional portal entry points for Creators and Staff', () => {
    const fixture = TestBed.createComponent(LearnerAuthModalComponent);
    component: fixture.componentInstance.open('login');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const portalLinks = compiled.querySelectorAll('.portal-link');
    expect(portalLinks.length).toBeGreaterThanOrEqual(2);
    const linkTexts = Array.from(portalLinks).map((el) => el.textContent || '');
    expect(linkTexts.some((t) => t.includes('Medical Reviewer') || t.includes('Contributor'))).toBe(true);
    expect(linkTexts.some((t) => t.includes('Municipal Staff') || t.includes('Case Management'))).toBe(true);
  });
});
