import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthenticationService } from './authentication.service';
import { User } from './user';
import { DjangoToken } from './django_token';

@Component({ selector: 'app', templateUrl: 'app.component.html' })
export class AppComponent {
  currentDjangoToken: DjangoToken;

  constructor(
    private router: Router,
    private authenticationService: AuthenticationService
  ) {
    this.authenticationService.currentDjangoToken.subscribe(
      x => (this.currentDjangoToken = x)
    );
  }

  logout() {
    this.authenticationService.logout();
    this.router.navigate(['/login']);
  }
}
