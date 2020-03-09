import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { User } from '../../shared/models/user';
import { Environment } from '../../../environments/environment-variables'

@Injectable({ providedIn: 'root' })
export class UserService {
  constructor(private http: HttpClient) {}

  getAll() {
    return this.http.get<User[]>(`${Environment.ANGULAR_DJANGO_AUTH_URL}/users`);
  }

  register(user: User) {
    return this.http.post(`${Environment.ANGULAR_DJANGO_AUTH_URL}/users/register`, user);
  }

  delete(id: number) {
    return this.http.delete(`${Environment.ANGULAR_DJANGO_AUTH_URL}/users/${id}`);
  }
}
