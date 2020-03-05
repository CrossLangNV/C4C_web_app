import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { DjangoToken } from './django_token';
import { Environment } from '../environments/environment-variables';

@Injectable({ providedIn: 'root' })
export class AuthenticationService {
  private currentDjangoTokenSubject: BehaviorSubject<DjangoToken>;
  public currentDjangoToken: Observable<DjangoToken>;

  constructor(private http: HttpClient) {
    this.currentDjangoTokenSubject = new BehaviorSubject<DjangoToken>(
      JSON.parse(localStorage.getItem('currentDjangoToken'))
    );
    this.currentDjangoToken = this.currentDjangoTokenSubject.asObservable();
  }

  public get currentDjangoTokenValue(): DjangoToken {
    return this.currentDjangoTokenSubject.value;
  }

  login(username, password) {
    let client_id = Environment.ANGULAR_DJANGO_CLIENT_ID;
    let client_secret = Environment.ANGULAR_DJANGO_CLIENT_SECRET;
    return this.http
      .post<any>(`${Environment.ANGULAR_DJANGO_AUTH_URL}/token`, {
        client_id,
        client_secret,
        username,
        password,
        grant_type: 'password'
      })
      .pipe(
        map(djangoToken => {
          // store user details and token in local storage to keep user logged in between page refreshes
          localStorage.setItem('currentDjangoToken', JSON.stringify(djangoToken));
          this.currentDjangoTokenSubject.next(djangoToken);
          return djangoToken;
        })
      );
  }

  signInWithGoogle(token) {
    let client_id = Environment.ANGULAR_DJANGO_CLIENT_ID;
    let client_secret = Environment.ANGULAR_DJANGO_CLIENT_SECRET;
    return this.http
      .post<any>(`${Environment.ANGULAR_DJANGO_AUTH_URL}/convert-token`, {
        client_id,
        client_secret,
        backend: 'google-oauth2',
        token,
        grant_type: 'convert_token'
      })
      .pipe(
        map(djangoToken => {
          // store user details and token in local storage to keep user logged in between page refreshes
          localStorage.setItem(
            'currentDjangoToken',
            JSON.stringify(djangoToken)
          );
          this.currentDjangoTokenSubject.next(djangoToken);
          return djangoToken;
        })
      );
  }

  logout() {
    // remove user from local storage and set current user to null
    localStorage.removeItem('currentDjangoToken');
    this.currentDjangoTokenSubject.next(null);
  }
}
