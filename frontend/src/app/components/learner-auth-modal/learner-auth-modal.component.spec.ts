import { TestBed } from '@angular/core/testing';
import { LearnerAuthModalComponent } from './learner-auth-modal.component';
import { LearnerAuthService } from '../../services/learner-auth.service';
import { LearningProgressService } from '../../services/learning-progress.service';

describe('LearnerAuthModalComponent', () => {
  let mockLearnerAuth: Partial<LearnerAuthService>;
  let mockProgressService: Partial<LearningProgressService>;

  beforeEach(async () => {
    mockLearnerAuth = {
      login: vi.fn().mockResolvedValue({ success: true, token: 'mock-jwt', user: { id: 'u1', name: 'Learner One' } }),
      register: vi.fn().mockResolvedValue({ success: true, token: 'mock-jwt', user: { id: 'u1', name: 'Learner One' } }),
      recover: vi.fn().mockResolvedValue({ success: true, message: 'Recovery sent.' }),
    };

    mockProgressService = {
      syncWithRemote: vi.fn().mockResolvedValue(undefined),
    };

    await TestBed.configureTestingModule({
      imports: [LearnerAuthModalComponent],
      providers: [
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
});
