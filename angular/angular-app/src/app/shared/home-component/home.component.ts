import { Component, OnInit } from '@angular/core';
import { first } from 'rxjs/operators';

import { User } from '../models/user';
import { DjangoUser } from '../models/django_user';
import { UserService } from '../../core/auth/user.service';
import { AuthenticationService } from '../../core/auth/authentication.service';

@Component({ templateUrl: 'home.component.html' })
export class HomeComponent implements OnInit {
  currentDjangoUser: DjangoUser;
  users = [];

  constructor(
    private authenticationService: AuthenticationService,
    private userService: UserService
  ) {
    this.currentDjangoUser = this.authenticationService.currentDjangoUserValue;
  }

  ngOnInit() {
    this.loadAllUsers();
  }

  deleteUser(id: number) {
    this.userService
      .delete(id)
      .pipe(first())
      .subscribe(() => this.loadAllUsers());
  }

  private loadAllUsers() {
    this.userService
      .getAll()
      .pipe(first())
      .subscribe(users => (this.users = users));
  }
}
