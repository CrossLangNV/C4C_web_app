import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Film } from './film';
import { Environment } from '../environments/environment-variables';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;

  constructor(private http: HttpClient) { }

  public getFilms(): Observable<Film[]> {
    return this.http.get<Film[]>(`${this.API_URL}/films`);
  }

  public searchFilms(term: string): Observable<Film[]> {
    return this.http.get<Film[]>(`${this.API_URL}/films/${term}`);
  }
}