import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Environment } from '../../../environments/environment-variables';
import { map } from 'rxjs/operators';
import { User, UserAdapter } from 'src/app/shared/models/user';

@Injectable({
  providedIn: 'root'
})
export class ApiAdminService {
  API_URL = Environment.ANGULAR_DJANGO_API_ADMIN_URL;

  constructor(private http: HttpClient, private userAdapter: UserAdapter) {}

  public getUsers(): Observable<User[]> {
    return this.http
      .get<User[]>(`${this.API_URL}auth/user`)
      .pipe(
        map((items: any[]) => items.map(item => this.userAdapter.adapt(item)))
      );
  }
}
