import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Website } from './website';
import { Environment } from '../environments/environment-variables';
import { SolrFile } from './solrfile';

@Injectable({
  providedIn: 'root'
})
export class ApiServiceWebsites {
  API_URL = "http://myhost:3001/";

  constructor(private http: HttpClient) {
  }

  public getWebsites(): Observable<Website[]> {
    return this.http.get<Website[]>(`${this.API_URL}/websites`);
  }

  public getWebsite(id: string): Observable<Website> {
    return this.http.get<Website>(`${this.API_URL}/websites/${id}`);
  }

  public searchWebsites(term: string): Observable<Website[]> {
    return this.http.get<Website[]>(`${this.API_URL}/websites/${term}`);
  }

  public deleteWebsite(id): Observable<any> {
    return this.http.delete(`${this.API_URL}/websites/delete/${id}`);
  }

  public updateWebsite(website: Website): Observable<Website> {
    return this.http.put<Website>(`${this.API_URL}/websites/${website.id}`, website);
  }
}

