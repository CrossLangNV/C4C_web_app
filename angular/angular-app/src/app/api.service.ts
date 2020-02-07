import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Film } from './film';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  API_URL = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  public getFilms(): Observable<Film[]> {
    return this.http.get<Film[]>(`${this.API_URL}/films`);
  }

  public searchFilms(term: string): Observable<Film[]> {
    return this.http.get<Film[]>(`${this.API_URL}/films/${term}`);
  }
}
