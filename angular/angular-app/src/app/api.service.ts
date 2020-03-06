import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Environment } from '../environments/environment-variables';
import { SolrFile, SolrFileAdapter } from './solrfile';
import { map } from 'rxjs/operators';
import { SolrDocument, SolrDocumentAdapter } from './solrdocument';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;

  constructor(
    private http: HttpClient,
    private solrFileAdapter: SolrFileAdapter,
    private solrDocumentAdapter: SolrDocumentAdapter
  ) {}

  public getSolrFiles(): Observable<SolrFile[]> {
    return this.http
      .get(`${this.API_URL}/solrfiles`)
      .pipe(
        map((data: any[]) => data.map(item => this.solrFileAdapter.adapt(item)))
      );
  }

  public searchSolrFiles(term: string): Observable<SolrFile[]> {
    return this.http
      .get<SolrFile[]>(`${this.API_URL}/solrfiles/${term}`)
      .pipe(
        map((data: any[]) => data.map(item => this.solrFileAdapter.adapt(item)))
      );
  }

  public getDocument(id: string): Observable<SolrDocument> {
    return this.http
      .get<SolrDocument>(`${this.API_URL}/solrdocument/${id}`)
      .pipe(
        map((data: any) =>
          data.map(item => this.solrDocumentAdapter.adapt(item))
        )
      );
  }
}
