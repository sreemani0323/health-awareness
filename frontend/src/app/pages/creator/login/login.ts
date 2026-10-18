import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { CreatorApiService } from '../../../services/creator-api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  username = '';
  password = '';
  errorMessage = '';
  isLoading = false;
  readonly isProduction = environment.production;

  constructor(
    private creatorApi: CreatorApiService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {
    // If already authenticated, redirect to role-tailored landing page
    if (this.creatorApi.isAuthenticated && this.creatorApi.currentUser) {
      this.routeToRoleLanding(this.creatorApi.currentUser.role);
    }
  }

  onSubmit(): void {
    if (!this.username.trim() || !this.password.trim()) {
      this.errorMessage = 'Please enter both username and password.';
      this.cdr.markForCheck();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.creatorApi.login({ username: this.username, password: this.password }).subscribe({
      next: (user) => {
        this.routeToRoleLanding(user.role);
      },
      error: (err: any) => {
        this.isLoading = false;
        this.errorMessage = err?.error?.error?.message || 'Login failed. Please check your credentials.';
        this.cdr.markForCheck();
      },
    });
  }

  private routeToRoleLanding(role: string): void {
    if (role === 'admin') {
      this.router.navigate(['/creator/admin']);
    } else if (role === 'reviewer') {
      this.router.navigate(['/creator/reviews']);
    } else {
      this.router.navigate(['/creator']);
    }
  }
}
