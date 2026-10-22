import { Component, signal, OnInit, OnDestroy, inject } from '@angular/core';
import { RouterOutlet, Router } from '@angular/router';
import { Location } from '@angular/common';
import { NavbarComponent } from './components/navbar/navbar.component';
import { FooterComponent } from './components/footer/footer.component';
import { Capacitor, PluginListenerHandle } from '@capacitor/core';
import { App as CapApp } from '@capacitor/app';
import { StatusBar, Style } from '@capacitor/status-bar';

@Component({
  selector: 'ha-root',
  standalone: true,
  imports: [RouterOutlet, NavbarComponent, FooterComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit, OnDestroy {
  readonly title = signal('HealthAware');
  private readonly router = inject(Router);
  private readonly location = inject(Location);
  private backButtonListener?: PluginListenerHandle;
  private appUrlListener?: PluginListenerHandle;

  async ngOnInit(): Promise<void> {
    if (!Capacitor.isNativePlatform()) {
      return;
    }

    try {
      await StatusBar.setStyle({ style: Style.Dark });
      await StatusBar.setBackgroundColor({ color: '#094142' });
    } catch {
      // Non-fatal if status bar styling is not supported in current environment
    }

    try {
      this.backButtonListener = await CapApp.addListener('backButton', ({ canGoBack }) => {
        // 1. Dismiss any open modal dialog or overlay
        const openModalCloseBtn = document.querySelector<HTMLElement>(
          '.modal-close, .auth-modal-close, [data-dismiss-modal], .mobile-menu-close, dialog[open] .close-btn, .dialog-close'
        );
        if (openModalCloseBtn) {
          openModalCloseBtn.click();
          return;
        }

        // 2. Dismiss open mobile navigation menu if open
        const mobileNavToggle = document.querySelector<HTMLElement>('.navbar-toggler[aria-expanded="true"]');
        if (mobileNavToggle) {
          mobileNavToggle.click();
          return;
        }

        // 3. Fallback to home or exit
        const currentUrl = this.router.url;
        if (currentUrl === '/' || currentUrl === '/home' || currentUrl === '') {
          CapApp.exitApp();
          return;
        }

        // 4. Navigate back in history or fallback to home
        if (canGoBack) {
          this.location.back();
        } else {
          this.router.navigate(['/']);
        }
      });

      this.appUrlListener = await CapApp.addListener('appUrlOpen', (event) => {
        try {
          const url = new URL(event.url);
          const path = url.pathname + url.search + url.hash;
          if (path) {
            this.router.navigateByUrl(path);
          }
        } catch {
          const cleanPath = event.url.replace(/^org\.healthaware\.app:\/\//, '/');
          this.router.navigateByUrl(cleanPath);
        }
      });
    } catch {
      // Non-fatal if native listener registration fails
    }
  }

  ngOnDestroy(): void {
    this.backButtonListener?.remove();
    this.appUrlListener?.remove();
  }
}

