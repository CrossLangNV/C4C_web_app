import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Website } from '../../shared/models/website';
import { Environment } from '../../../environments/environment-variables';

@Injectable({
  providedIn: 'root'
})
export class ApiServiceWebsites {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;

  constructor(private http: HttpClient) {
  }

  public getWebsites(): Observable<Website[]> {
    return this.http.get<Website[]>(`${this.API_URL}/website`);
  }

  public getWebsite(id: string): Observable<Website> {
    return this.http.get<Website>(`${this.API_URL}/website/${id}`);
  }

  public deleteWebsite(id): Observable<any> {
    return this.http.delete(`${this.API_URL}/website/${id}`);
  }

  public updateWebsite(website: Website): Observable<Website> {
    return this.http.put<Website>(`${this.API_URL}/website/${website.id}/`, website);
  }
}

