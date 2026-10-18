import { Component, Input, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { CreatorApiService } from '../../services/creator-api.service';
import { AuthUser } from '../../models/creator.models';

@Component({
  selector: 'app-creator-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './creator-navbar.component.html',
  styleUrl: './creator-navbar.component.css',
})
export class CreatorNavbarComponent implements OnInit {
  @Input() currentSection: string = 'dashboard';
  @Input() pendingReviewCount: number = 0;

  currentUser: AuthUser | null = null;
  mobileMenuOpen = false;

  constructor(
    public creatorApi: CreatorApiService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.creatorApi.currentUser$.subscribe((user) => {
      this.currentUser = user;
      this.cdr.markForCheck();
      if (this.canReview && this.pendingReviewCount === 0) {
        this.fetchPendingReviewsCount();
      }
    });
  }

  get canReview(): boolean {
    return this.currentUser?.role === 'reviewer' || this.currentUser?.role === 'admin';
  }

  get canCreate(): boolean {
    return this.currentUser?.role === 'contributor' || this.currentUser?.role === 'admin';
  }

  get isAdmin(): boolean {
    return this.currentUser?.role === 'admin';
  }

  get isReviewer(): boolean {
    return this.currentUser?.role === 'reviewer';
  }

  get isContributor(): boolean {
    return this.currentUser?.role === 'contributor';
  }

  get homeRoute(): string {
    if (this.isAdmin) return '/creator/admin';
    if (this.isReviewer) return '/creator/reviews';
    return '/creator';
  }

  fetchPendingReviewsCount(): void {
    this.creatorApi.getReviewQueue().subscribe({
      next: (items) => {
        this.pendingReviewCount = items.length;
        this.cdr.markForCheck();
      },
      error: () => {},
    });
  }

  toggleMobileMenu(): void {
    this.mobileMenuOpen = !this.mobileMenuOpen;
  }

  logout(): void {
    this.creatorApi.logout().subscribe({
      next: () => this.router.navigate(['/creator/login']),
    });
  }
}
