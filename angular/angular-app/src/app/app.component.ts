import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthenticationService } from './authentication.service';
import { User } from './user';
import { DjangoUser } from './django_user';

@Component({ selector: 'app', templateUrl: 'app.component.html' })
export class AppComponent {
  currentDjangoUser: DjangoUser;

  constructor(
    private router: Router,
    private authenticationService: AuthenticationService
  ) {
    this.authenticationService.currentDjangoUser.subscribe(
      x => (this.currentDjangoUser = x)
    );
  }

  logout() {
    this.authenticationService.logout();
    this.router.navigate(['/login']);
  }
}
