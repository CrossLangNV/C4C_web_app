import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { Environment } from '../../../environments/environment-variables';
import { SolrFile, SolrFileAdapter } from '../../shared/models/solrfile';
import { map, flatMap } from 'rxjs/operators';
import {
  Document,
  DocumentAdapter,
  DocumentResults,
} from '../../shared/models/document';
import { Website, WebsiteAdapter } from '../../shared/models/website';
import { Attachment, AttachmentAdapter } from '../../shared/models/attachment';
import { of } from 'rxjs';
import {
  AcceptanceState,
  AcceptanceStateAdapter,
} from 'src/app/shared/models/acceptanceState';
import { Comment, CommentAdapter } from 'src/app/shared/models/comment';
import { Tag, TagAdapter } from 'src/app/shared/models/tag';
import {
  Concept,
  ConceptAdapter,
  ConceptResults,
} from 'src/app/shared/models/concept';
import {
  ConceptTag,
  ConceptTagAdapter,
} from 'src/app/shared/models/ConceptTag';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;
  API_GLOSSARY_URL = Environment.ANGULAR_DJANGO_API_GLOSSARY_URL;

  messageSource: Subject<string>;

  constructor(
    private http: HttpClient,
    private solrFileAdapter: SolrFileAdapter,
    private documentAdapter: DocumentAdapter,
    private websiteAdapter: WebsiteAdapter,
    private attachmentAdapter: AttachmentAdapter,
    private stateAdapter: AcceptanceStateAdapter,
    private commentAdapter: CommentAdapter,
    private tagAdapter: TagAdapter,
    private conceptTagAdapter: ConceptTagAdapter,
    private conceptAdapter: ConceptAdapter
  ) {
    this.messageSource = new Subject<string>();
  }

  public getSolrFiles(pageNumber: number, pageSize: number): Observable<any[]> {
    return this.http
      .get<any[]>(
        `${this.API_URL}/solrfiles/?pageNumber=${pageNumber}&pageSize=${pageSize}`
      )
      .pipe(
        map((data: any[]) => {
          const result = [data[0]];
          result.push(data[1].map((item) => this.solrFileAdapter.adapt(item)));
          return result;
        })
      );
  }

  public searchSolrFiles(
    pageNumber: number,
    pageSize: number,
    term: string
  ): Observable<any[]> {
    return this.http
      .get<any[]>(
        `${this.API_URL}/solrfiles/${term}?pageNumber=${pageNumber}&pageSize=${pageSize}`
      )
      .pipe(
        map((data: any[]) => {
          const result = [data[0]];
          result.push(data[1].map((item) => this.solrFileAdapter.adapt(item)));
          return result;
        })
      );
  }

  public searchSolrDocuments(
    pageNumber: number,
    pageSize: number,
    term: string,
    idsFilter: string[]
  ): Observable<any[]> {
    let requestUrl = `${this.API_URL}/solrdocument/search/${term}?pageNumber=${pageNumber}&pageSize=${pageSize}`;
    idsFilter.forEach((id) => {
      requestUrl += `&id=${id}`;
    });
    return this.http.get<any[]>(requestUrl).pipe(
      map((data: any[]) => {
        const result = [data[0]];
        result.push(data[1]);
        return result;
      })
    );
  }

  public getWebsites(): Observable<Website[]> {
    // return of([
    //   new Website("1", "Staatsblad", "htp://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"]),
    //   new Website("1", "Staatsblad", "htp://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"]),
    // ]);
    return this.http
      .get<Website[]>(`${this.API_URL}/websites`)
      .pipe(
        map((data: any[]) =>
          data.map((item) => this.websiteAdapter.adapt(item))
        )
      );
  }

  public getWebsite(id: string): Observable<Website> {
    // return of(
    //   new Website("1", "Staatsblad", "htp://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"])
    // );
    return this.http
      .get<Website>(`${this.API_URL}/website/${id}`)
      .pipe(map((item) => this.websiteAdapter.adapt(item)));
  }

  public createWebsite(website: Website): Observable<any> {
    // return of([
    //   new Website("1", "name", "htp://url", "bla", []),
    // ]);
    return this.http.post<Website>(
      `${this.API_URL}/websites`,
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
      `${this.API_URL}/website/${website.id}`,
      this.websiteAdapter.encode(website)
    );
  }

  public getDocumentResults(
    page: number,
    searchTerm: string,
    filterType: string,
    email: string,
    website: string,
    showOnlyOwn: boolean,
    filterTag: string,
    sortBy: string
  ): Observable<DocumentResults> {
    var pageQuery = page ? '?page=' + page : '';
    if (searchTerm) {
      pageQuery = pageQuery + '&keyword=' + searchTerm;
    }
    if (filterType) {
      pageQuery = pageQuery + '&filterType=' + filterType;
    }
    if (email) {
      pageQuery = pageQuery + '&email=' + email;
    }
    if (website && website != 'none') {
      pageQuery = pageQuery + '&website=' + website;
    }
    if (showOnlyOwn) {
      pageQuery = pageQuery + '&showOnlyOwn=' + showOnlyOwn;
    }
    if (filterTag) {
      pageQuery = pageQuery + '&tag=' + filterTag;
    }
    if (sortBy) {
      pageQuery = pageQuery + '&ordering=' + sortBy;
    }
    return this.http.get<DocumentResults>(
      `${this.API_URL}/documents${pageQuery}`
    );
  }

  public getDocuments(page: Number): Observable<Document[]> {
    var pageQuery = page ? '?page=' + page : '';
    return this.http
      .get<Document[]>(`${this.API_URL}/documents${pageQuery}`)
      .pipe(
        map((data: any[]) =>
          data['results'].map((item) => this.documentAdapter.adapt(item))
        )
      );
  }

  public getDocument(id: string): Observable<Document> {
    // return of(
    //   new Document("id", "title", "titlePrefix", "type", new Date(), "accepted", "http://www.document.be", "http://staatsblad.be", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", "Belgisch Staatsblad Het Belgisch Staatsblad (BS) produceert en verspreidt een brede waaier officiële en overheidspublicaties. Het doet dat zowel via traditionele (papier) als elektronische (internet) kanalen. Voor de belangrijkste officiële publicaties gebeurt de distributie enkel via elektronische weg. Het BS biedt een aantal databanken aan waarvan het Belgisch Staatsblad(externe link) zelf, de bijlage van de rechtspersonen(externe link), de openbare aanbestedingen(externe link) (tot 31 december 2010) en de Justel-databanken(externe link) (geconsolideerde wetgeving en wetgevingsindex) de meest bekende zijn. Daarnaast geven de diensten van het BS beknopte informatie over gegevens die in de publicaties zijn verschenen. Het BS helpt ook bij de distributie van een breed gamma informatiebrochures uitgegeven door de FOD Justitie.", ["1", "2"])
    // );
    if (id) {
      return this.http
        .get<Document>(`${this.API_URL}/document/${id}`)
        .pipe(map((item) => this.documentAdapter.adapt(item)));
    } else {
      return of(null);
    }
  }

  public getDocumentSyncWithAttachments(id: string): Observable<Document> {
    return this.http
      .get<Document>(
        `${this.API_URL}/document/${id}?sync=true&with_attachments=true`
      )
      .pipe(map((item) => this.documentAdapter.adapt(item)));
  }

  public createDocument(document: Document): Observable<Document> {
    return this.http
      .post<Document>(
        `${this.API_URL}/documents`,
        this.documentAdapter.encode(document)
      )
      .pipe(map((item) => this.documentAdapter.adapt(item)));
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
      .pipe(map((item) => this.attachmentAdapter.adapt(item)));
  }

  public addAttachment(formData: FormData): Observable<Attachment> {
    return this.http.post<Attachment>(`${this.API_URL}/attachments`, formData);
  }

  public deleteAttachment(id: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/attachment/${id}`);
  }

  public getSolrDocument(id: string): Observable<any> {
    return this.http.get<any>(`${this.API_URL}/solrdocument/${id}`);
  }

  public getEURLEXxhtml(celex_id: string): Observable<any> {
    return this.http.get<string[]>(
      `${this.API_URL}/celex?celex_id=${celex_id}`
    );
  }

  public getDocumentStats(): Observable<any> {
    return this.http.get<string[]>(`${this.API_URL}/stats`);
  }

  public getStateValues(): Observable<string[]> {
    return this.http.get<string[]>(`${this.API_URL}/state/value`);
  }

  public getState(id: string): Observable<AcceptanceState> {
    return this.http
      .get<AcceptanceState>(`${this.API_URL}/state/${id}`)
      .pipe(map((item) => this.stateAdapter.adapt(item)));
  }

  public getComment(id: string): Observable<Comment> {
    return this.http
      .get<Comment>(`${this.API_URL}/comment/${id}`)
      .pipe(map((item) => this.commentAdapter.adapt(item)));
  }

  public addComment(comment: Comment): Observable<Comment> {
    return this.http
      .post<Comment>(
        `${this.API_URL}/comments`,
        this.commentAdapter.encode(comment)
      )
      .pipe(map((item) => this.commentAdapter.adapt(item)));
  }

  public deleteComment(id: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/comment/${id}`);
  }

  public addTag(tag: Tag): Observable<Tag> {
    return this.http
      .post<Tag>(`${this.API_URL}/tags`, this.tagAdapter.encode(tag))
      .pipe(map((item) => this.tagAdapter.adapt(item)));
  }

  public deleteTag(id: string): Observable<any> {
    return this.http.delete(`${this.API_URL}/tag/${id}`);
  }

  public updateState(state: AcceptanceState): Observable<AcceptanceState> {
    return this.http.put<AcceptanceState>(
      `${this.API_URL}/state/${state.id}`,
      this.stateAdapter.encode(state)
    );
  }

  public isAdmin(): Observable<boolean> {
    return this.http.get<boolean>(`${this.API_URL}/super`);
  }

  //
  // GLOSSARY //
  //

  public getConcepts(
    page: number,
    searchTerm: string,
    filterTag: string,
    filterType: string,
    sortBy: string
  ): Observable<ConceptResults> {
    var pageQuery = page ? '?page=' + page : '';
    if (searchTerm) {
      pageQuery = pageQuery + '&keyword=' + searchTerm;
    }
    if (filterType) {
      pageQuery = pageQuery + '&filterType=' + filterType;
    }
    if (filterTag) {
      pageQuery = pageQuery + '&tag=' + filterTag;
    }
    if (sortBy) {
      pageQuery = pageQuery + '&ordering=' + sortBy;
    }
    return this.http.get<ConceptResults>(
      `${this.API_GLOSSARY_URL}/concepts${pageQuery}`
    );
  }

  public getConcept(id: string): Observable<Concept> {
    return this.http
      .get<Concept>(`${this.API_GLOSSARY_URL}/concept/${id}`)
      .pipe(map((item) => this.conceptAdapter.adapt(item)));
  }

  public getConceptComment(id: string): Observable<Comment> {
    return this.http
      .get<Comment>(`${this.API_GLOSSARY_URL}/comment/${id}`)
      .pipe(map((item) => this.commentAdapter.adapt(item)));
  }

  public addConceptComment(comment: Comment): Observable<Comment> {
    return this.http
      .post<Comment>(
        `${this.API_GLOSSARY_URL}/comments`,
        this.commentAdapter.encode(comment)
      )
      .pipe(map((item) => this.commentAdapter.adapt(item)));
  }

  public deleteConceptComment(id: string): Observable<any> {
    return this.http.delete(`${this.API_GLOSSARY_URL}/comment/${id}`);
  }

  public addConceptTag(tag: ConceptTag): Observable<ConceptTag> {
    return this.http
      .post<ConceptTag>(
        `${this.API_GLOSSARY_URL}/tags`,
        this.conceptTagAdapter.encode(tag)
      )
      .pipe(map((item) => this.conceptTagAdapter.adapt(item)));
  }

  public deleteConceptTag(id: string): Observable<any> {
    return this.http.delete(`${this.API_GLOSSARY_URL}/tag/${id}`);
  }
}
