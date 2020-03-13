import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Environment } from '../../../environments/environment-variables';
import { SolrFile, SolrFileAdapter } from '../../shared/models/solrfile';
import { map } from 'rxjs/operators';
import { Document, DocumentAdapter } from '../../shared/models/document';
import { Website, WebsiteAdapter } from '../../shared/models/website';
import { Attachment, AttachmentAdapter } from '../../shared/models/attachment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;

  constructor(
    private http: HttpClient,
    private solrFileAdapter: SolrFileAdapter,
    private documentAdapter: DocumentAdapter,
    private websiteAdapter: WebsiteAdapter,
    private attachmentAdapter: AttachmentAdapter
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

  public getWebsites(): Observable<Website[]> {
    return this.http.get<Website[]>(`${this.API_URL}/website`);
  }

  public getWebsite(id: string): Observable<Website> {
    return this.http
      .get<Website>(`${this.API_URL}/website/${id}`)
      .pipe(map(item => this.websiteAdapter.adapt(item)));
  }

  public deleteWebsite(id): Observable<any> {
    return this.http.delete(`${this.API_URL}/website/${id}`);
  }

  public updateWebsite(website: Website): Observable<Website> {
    return this.http.put<Website>(
      `${this.API_URL}/website/${website.id}/`,
      website
    );
  }

  public getDocument(id: string): Observable<Document> {
    return this.http
      .get<Document>(`${this.API_URL}/document/${id}`)
      .pipe(map(item => this.documentAdapter.adapt(item)));
  }

  public getAttachment(id: string): Observable<Attachment> {
    return this.http
      .get<Attachment>(`${this.API_URL}/attachment/${id}`)
      .pipe(map(item => this.attachmentAdapter.adapt(item)));
  }
}
