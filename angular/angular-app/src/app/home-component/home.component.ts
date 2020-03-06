import { Component, OnInit } from '@angular/core';
import { first } from 'rxjs/operators';

import { User } from '../user';
import { DjangoUser } from '../django_user';
import { UserService } from '../user.service';
import { AuthenticationService } from '../authentication.service';

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
