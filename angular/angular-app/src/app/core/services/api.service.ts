import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Environment } from '../../../environments/environment-variables';
import { SolrFile, SolrFileAdapter } from '../../shared/models/solrfile';
import { map } from 'rxjs/operators';
import { Document, DocumentAdapter } from '../../shared/models/document';
import { Website, WebsiteAdapter } from '../../shared/models/website';
import { Attachment, AttachmentAdapter } from '../../shared/models/attachment';
import { of } from 'rxjs';
import {
  AcceptanceState,
  AcceptanceStateAdapter
} from 'src/app/shared/models/acceptanceState';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;
  //API_URL = 'localhost:3001';

  constructor(
    private http: HttpClient,
    private solrFileAdapter: SolrFileAdapter,
    private documentAdapter: DocumentAdapter,
    private websiteAdapter: WebsiteAdapter,
    private attachmentAdapter: AttachmentAdapter,
    private stateAdapter: AcceptanceStateAdapter
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
    // return of([
    //   new Website("1", "Staatsblad", "htp://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"]),
    //   new Website("1", "Staatsblad", "htp://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"]),
    // ]);
    return this.http.get<Website[]>(`${this.API_URL}/website`);
  }

  public getWebsite(id: string): Observable<Website> {
    // return of(
    //   new Website("1", "Staatsblad", "htp://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"])
    // );
    return this.http
      .get<Website>(`${this.API_URL}/website/${id}`)
      .pipe(map(item => this.websiteAdapter.adapt(item)));
  }

  public createWebsite(website: Website): Observable<any> {
    // return of([
    //   new Website("1", "name", "htp://url", "bla", []),
    // ]);
    return this.http.post<Website>(
      `${this.API_URL}/website/`,
      this.websiteAdapter.encode(website)
    );
  }

  public deleteWebsite(id): Observable<any> {
    // return of([
    //   new Website("1", "name", "htp://url", "bla", []),
    // ]);
    return this.http.delete(`${this.API_URL}/website/${id}`);
  }

  public updateWebsite(website: Website): Observable<Website> {
    return this.http.put<Website>(
      `${this.API_URL}/website/${website.id}/`,
      this.websiteAdapter.encode(website)
    );
  }

  public getDocument(id: string): Observable<Document> {
    // return of(
    //   new Document("id", "title", "titlePrefix", "type", new Date(), "accepted", "http://www.document.be", "http://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"])
    // );
    return this.http
      .get<Document>(`${this.API_URL}/document/${id}`)
      .pipe(map(item => this.documentAdapter.adapt(item)));
  }

  public createDocument(document: Document): Observable<Document> {
    return this.http
      .post<Document>(
        `${this.API_URL}/document/`,
        this.documentAdapter.encode(document)
      )
      .pipe(map(item => this.documentAdapter.adapt(item)));
  }

  public deleteDocument(id: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/document/${id}`);
  }

  public updateDocument(document: Document): Observable<Document> {
    return this.http.put<Document>(
      `${this.API_URL}/document/${document.id}/`,
      this.documentAdapter.encode(document)
    );
  }

  public getAttachment(id: string): Observable<Attachment> {
    return this.http
      .get<Attachment>(`${this.API_URL}/attachment/${id}`)
      .pipe(map(item => this.attachmentAdapter.adapt(item)));
  }

  public addAttachment(formData: FormData): Observable<Attachment> {
    return this.http.post<Attachment>(`${this.API_URL}/attachment/`, formData);
  }

  public deleteAttachment(id: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/attachment/${id}`);
  }

  public getStateValues(): Observable<string[]> {
    return this.http.get<string[]>(`${this.API_URL}/state/value`);
  }

  public getState(id: string): Observable<AcceptanceState> {
    return this.http
      .get<AcceptanceState>(`${this.API_URL}/state/${id}`)
      .pipe(map(item => this.stateAdapter.adapt(item)));
  }

  public updateState(state: AcceptanceState): Observable<AcceptanceState> {
    return this.http.put<AcceptanceState>(
      `${this.API_URL}/state/${state.id}/`,
      this.stateAdapter.encode(state)
    );
  }

  public isAdmin(): Observable<boolean> {
    return this.http.get<boolean>(`${this.API_URL}/super`);
  }
}
