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
import { Bookmark, BookmarkAdapter } from 'src/app/shared/models/Bookmark';
import {
  Concept,
  ConceptAdapter,
  ConceptResults,
} from 'src/app/shared/models/concept';
import {
  ConceptTag,
  ConceptTagAdapter,
} from 'src/app/shared/models/ConceptTag';
import {
  RoResults,
  ReportingObligation,
  RoAdapter,
} from 'src/app/shared/models/ro';
import * as rosData from './ros.json';
import {ConceptAcceptanceState, ConceptAcceptanceStateAdapter} from "../../shared/models/conceptAcceptanceState";
import {ConceptComment, ConceptCommentAdapter} from "../../shared/models/conceptComment";
import {RdfEntity} from "../../shared/models/rdfEntity";
import {RdfFilter} from "../../shared/models/rdfFilter";
import {RoTag, RoTagAdapter} from "../../shared/models/RoTag";
import {RoAcceptanceState, RoAcceptanceStateAdapter} from "../../shared/models/roAcceptanceState";
import {RoComment, RoCommentAdapter} from "../../shared/models/roComment";
import { DjangoUser } from 'src/app/shared/models/django_user';
import {DropdownOption} from '../../shared/models/DropdownOption';
import {PublicService, PublicServiceAdapter, PublicServiceResults} from '../../shared/models/PublicService';
import {ContactPoint, ContactPointAdapter, ContactPointResults} from '../../shared/models/ContactPoint';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;
  API_GLOSSARY_URL = Environment.ANGULAR_DJANGO_API_GLOSSARY_URL;
  API_RO_URL = Environment.ANGULAR_DJANGO_API_RO_URL;
  API_CPSV_URL = Environment.ANGULAR_DJANGO_API_CPSV_URL;
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
    private conceptAdapter: ConceptAdapter,
    private conceptAcceptanceStateAdapter: ConceptAcceptanceStateAdapter,
    private conceptCommentAdapter: ConceptCommentAdapter,
    private roAdapter: RoAdapter,
    private psAdapter: PublicServiceAdapter,
    private cpAdapter: ContactPointAdapter,
    private roTagAdapter: RoTagAdapter,
    private roAcceptanceStateAdapter: RoAcceptanceStateAdapter,
    private roCommentAdapter: RoCommentAdapter,
    private bookmarkAdapter: BookmarkAdapter,
  ) {
    this.messageSource = new Subject<string>();
  }

  public searchSolrDocuments(
    pageNumber: number,
    pageSize: number,
    term: string,
    idsFilter: string[],
    sortBy: string,
    sortDirection: string
  ): Observable<any[]> {
    let requestUrl = `${this.API_URL}/solrdocument/search/${term}?pageNumber=${pageNumber}&pageSize=${pageSize}`;
    idsFilter.forEach((id) => {
      requestUrl += `&id=${id}`;
    });
    if (sortBy) {
      requestUrl += `&sortBy=${sortBy}`;
      if (sortDirection) {
        requestUrl += `&sortDirection=${sortDirection}`;
      }
    }
    return this.http.get<any[]>(requestUrl).pipe(
      map((data: any[]) => {
        const result = [data[0]];
        result.push(data[1]);
        return result;
      })
    );
  }

  public searchSolrPreAnalyzedDocuments(
    pageNumber: number,
    pageSize: number,
    term: string,
    field: string,
    idsFilter: string[],
    sortBy: string,
    sortDirection: string
  ): Observable<any[]> {
    let requestUrl = `${this.API_URL}/solrdocument/search/query/preanalyzed/`;
    // let requestUrl = `http://localhost:8983/solr/documents/select?hl.fl=${field}&hl=on&q={!term f=${field}}${term}`;

    if (sortBy) {
      requestUrl += `?sortBy=${sortBy}`;
      if (sortDirection) {
        requestUrl += `&sortDirection=${sortDirection}`;
      }
      if (pageNumber) {
        requestUrl += `&pageNumber=${pageNumber}`;
      }
      if (pageSize) {
        requestUrl += `&pageSize=${pageSize}`;
      }
    }

    let formData = new FormData();
    formData.append('query', `{!term f=${field}}${term}`);

    return this.http.post<any[]>(requestUrl, formData).pipe(
      map((data: any[]) => {
        const result = [data[0]];
        result.push(data[1]);
        return result;
      })
    );
  }

  public searchSolrPreAnalyzedDocument(
    docId: string,
    pageNumber: number,
    pageSize: number,
    term: string,
    field: string,
    idsFilter: string[],
    sortBy: string,
    sortDirection: string
  ): Observable<any[]> {
    let requestUrl = `${this.API_URL}/solrdocument/search/query/preanalyzed/` + docId;
    // let requestUrl = `http://localhost:8983/solr/documents/select?hl.fl=${field}&hl=on&q={!term f=${field}}${term}` + docId;

    if (sortBy) {
      requestUrl += `?sortBy=${sortBy}`;
      if (sortDirection) {
        requestUrl += `&sortDirection=${sortDirection}`;
      }
      if (pageNumber) {
        requestUrl += `&pageNumber=${pageNumber}`;
      }
      if (pageSize) {
        requestUrl += `&pageSize=${pageSize}`;
      }
    }

    let formData = new FormData();
    formData.append('query', `{!term f=${field}}${term}`);

    return this.http.post<any[]>(requestUrl, formData).pipe(
      map((data: any[]) => {
        const result = [data[0]];
        result.push(data[1]);
        return result;
      })
    );
  }

  public getDjangoAndSolrPrAnalyzedDocuments(
    pageNumber: number,
    pageSize: number,
    term: string,
    field: string,
    conceptId: string,
    idsFilter: string[],
    sortBy: string,
    sortDirection: string
  ): Observable<any[]> {
    let requestUrl = `${this.API_URL}/solrdocument/search/query/django/`;
    // let requestUrl = `http://localhost:8983/solr/documents/select?hl.fl=${field}&hl=on&q={!term f=${field}}${term}`;

    if (sortBy) {
      requestUrl += `?sortBy=${sortBy}`;
      if (sortDirection) {
        requestUrl += `&sortDirection=${sortDirection}`;
      }
      if (pageNumber) {
        requestUrl += `&pageNumber=${pageNumber}`;
      }
      if (pageSize) {
        requestUrl += `&pageSize=${pageSize}`;
      }
    }

    // let formData = new FormData();
    // formData.append('field', field);
    // formData.append('term', term);

    return this.http.post<any[]>(requestUrl, {'field': field, 'term': term, 'id': conceptId}).pipe(
      map((data: any[]) => {
        const result = [data[0]];
        result.push(data[1]);
        return result;
      })
    );
  }

  public getSolrDocumentContent(documentId: string): Observable<string> {
    const requestUrl = `${this.API_URL}/solrdocument/${documentId}`;
    return this.http.get<any[]>(requestUrl).pipe(
      map((data: any[]) => {
        const doc = data[0];
        return doc.content[0];
      })
    );
  }

  public getSolrDocumentHTMLContent(documentId: string): Observable<string> {
    const requestUrl = `${this.API_URL}/solrdocument/${documentId}`;
    return this.http.get<any[]>(requestUrl).pipe(
      map((data: any[]) => {
        const doc = data[0];
        return doc.content_html[0];
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

  public createDocument(formData: FormData): Observable<Document> {
    return this.http
      .post<Document>( `${this.API_URL}/documents`, formData)
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

  public getDocumentWithContent(id: string): Observable<Document> {
    return this.http
      .get<Document>(`${this.API_URL}/document/${id}?with_content=true`)
      .pipe(map((item) => this.documentAdapter.adapt(item)));
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

  public getDocumentStats(): Observable<any> {
    return this.http.get<string[]>(`${this.API_URL}/stats`);
  }

  public getSimilarDocuments(id: string, threshold: number, numberCandidates: number): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.API_URL}/solrdocuments/like/${id}?threshold=${threshold}&numberCandidates=${numberCandidates}`
    );
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

  // Returns a comment because comment is also compatible
  public addBookmark(user: DjangoUser, document: Document): Observable<Comment> {
    document.bookmark=false;
    let b = new Bookmark(user.username,document);
    return this.http
      .post<Document>(
        `${this.API_URL}/bookmarks`,
        this.bookmarkAdapter.encode(b)
      )
      .pipe(map((item) => this.commentAdapter.adapt(item)));
  }

  public removeBookmark(document: Document): Observable<any> {
    return this.http.delete(`${this.API_URL}/bookmarks/${document.id}`);
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
    return this.http.post<AcceptanceState>(
      `${this.API_URL}/states`,
      this.stateAdapter.encode(state)
    );
  }

  public isAdmin(): Observable<boolean> {
    return this.http.get<boolean>(`${this.API_URL}/super`);
  }

  //
  // GLOSSARY //
  //

  public getConceptVersions(): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.API_GLOSSARY_URL}/concepts/versions`
    );
  }

  public getConcepts(
    page: number,
    searchTerm: string,
    filterTag: string,
    filterType: string,
    version: string,
    showBookmarked: boolean,
    email: string,
    website: string,
    sortBy: string
  ): Observable<ConceptResults> {
    var pageQuery = page ? '?page=' + page : '';
    if (searchTerm) {
      pageQuery = pageQuery + '&keyword=' + searchTerm;
    }
    if (filterType) {
      pageQuery = pageQuery + '&filterType=' + filterType;
    }
    if (version) {
      pageQuery = pageQuery + '&version=' + version;
    }
    if (showBookmarked) {
      pageQuery = pageQuery + '&showBookmarked=' + showBookmarked;
    }
    if (email) {
      pageQuery = pageQuery + '&email=' + email;
    }
    if (website) {
      pageQuery = pageQuery + '&website=' + website;
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

  public getConceptComment(id: string): Observable<ConceptComment> {
    return this.http
      .get<ConceptComment>(`${this.API_GLOSSARY_URL}/comment/${id}`)
      .pipe(map((item) => this.conceptCommentAdapter.adapt(item)));
  }

  public addConceptComment(comment: ConceptComment): Observable<ConceptComment> {
    return this.http
      .post<ConceptComment>(
        `${this.API_GLOSSARY_URL}/comments`,
        this.conceptCommentAdapter.encode(comment)
      )
      .pipe(map((item) => this.conceptCommentAdapter.adapt(item)));
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

  public getConceptStateValues(): Observable<string[]> {
    return this.http.get<string[]>(`${this.API_GLOSSARY_URL}/state/value`);
  }

  public getConceptState(id: string): Observable<ConceptAcceptanceState> {
    return this.http
      .get<ConceptAcceptanceState>(`${this.API_GLOSSARY_URL}/state/${id}`)
      .pipe(map((item) => this.conceptAcceptanceStateAdapter.adapt(item)));
  }

  public updateConceptState(state: ConceptAcceptanceState): Observable<ConceptAcceptanceState> {
    return this.http.put<ConceptAcceptanceState>(
      `${this.API_GLOSSARY_URL}/state/${state.id}`,
      this.conceptAcceptanceStateAdapter.encode(state)
    );
  }

  //
  // REPORING OBLIGATIONS //
  //

  public getRos(
    page: number,
    searchTerm: string,
    filterTag: string,
    filterType: string,
    sortBy: string
  ): Observable<RoResults> {
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
    return this.http.get<RoResults>(
      `${this.API_RO_URL}/ros${pageQuery}`
    );

  }

  public getRdfRos(
    page: number,
    searchTerm: string,
    filterTag: string,
    filterType: string,
    sortBy: string,
    rdfFilters: Map<string, string>
  ): Observable<RoResults> {
    var pageQuery = page ? '?page=' + page : '';
    // Convert Map to an array as Typescript Maps cannot be used directly in a http post
    let rdfFiltersMap = {};
    rdfFilters.forEach((val: string, key: string) => {
      rdfFiltersMap[key] = val;
    });
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
    return this.http.post<RoResults>(
      `${this.API_RO_URL}/rdf_ros${pageQuery}`, {"rdfFilters": rdfFiltersMap}
    );

  }

  public getRo(id: string): Observable<ReportingObligation> {
    return this.http
      .get<ReportingObligation>(`${this.API_RO_URL}/ro/${id}`)
      .pipe(map((item) => this.roAdapter.adapt(item)));
  }

  // RO States/comments/tags
  public addRoTag(tag: RoTag): Observable<RoTag> {
    return this.http
      .post<RoTag>(
        `${this.API_RO_URL}/tags`,
        this.roTagAdapter.encode(tag)
      )
      .pipe(map((item) => this.roTagAdapter.adapt(item)));
  }

  public deleteRoTag(id: string): Observable<any> {
    return this.http.delete(`${this.API_RO_URL}/tag/${id}`);
  }

  public getRoStateValues(): Observable<string[]> {
    return this.http.get<string[]>(`${this.API_RO_URL}/state/value`);
  }

  public getRoState(id: string): Observable<RoAcceptanceState> {
    return this.http
      .get<RoAcceptanceState>(`${this.API_RO_URL}/state/${id}`)
      .pipe(map((item) => this.roAcceptanceStateAdapter.adapt(item)));
  }

  public updateRoState(state: RoAcceptanceState): Observable<RoAcceptanceState> {
    return this.http.put<RoAcceptanceState>(
      `${this.API_RO_URL}/state/${state.id}`,
      this.roAcceptanceStateAdapter.encode(state)
    );
  }

  public getRoComment(id: string): Observable<RoComment> {
    return this.http
      .get<RoComment>(`${this.API_RO_URL}/comment/${id}`)
      .pipe(map((item) => this.roCommentAdapter.adapt(item)));
  }

  public addRoComment(comment: RoComment): Observable<RoComment> {
    return this.http
      .post<RoComment>(
        `${this.API_RO_URL}/comments`,
        this.roCommentAdapter.encode(comment)
      )
      .pipe(map((item) => this.roCommentAdapter.adapt(item)));
  }

  public deleteRoComment(id: string): Observable<any> {
    return this.http.delete(`${this.API_RO_URL}/comment/${id}`);
  }

  public getWebAnnoLink(id: string): Observable<string> {
    return this.http.get<string>(
      `${this.API_GLOSSARY_URL}/webanno_link/${id}`
    );
  }

  public fetchCelexOptions(): Observable<DropdownOption[]> {
    return this.http.get<DropdownOption[]>(`${this.API_URL}/filters/celex`)
  }

  public fetchTypeOptions(): Observable<DropdownOption[]> {
    return this.http.get<DropdownOption[]>(`${this.API_URL}/filters/type`)
  }

  public fetchStatusOptions(): Observable<DropdownOption[]> {
    return this.http.get<DropdownOption[]>(`${this.API_URL}/filters/status`)
  }

  public fetchEliOptions(): Observable<DropdownOption[]> {
    return this.http.get<DropdownOption[]>(`${this.API_URL}/filters/eli`)
  }

  public fetchAuthorOptions(): Observable<DropdownOption[]> {
    return this.http.get<DropdownOption[]>(`${this.API_URL}/filters/author`)
  }

  public fetchEffectDateOptions(): Observable<DropdownOption[]> {
    return this.http.get<DropdownOption[]>(`${this.API_URL}/filters/effectdate`)
  }

  public getReportingObligationsView(id: string): Observable<string> {
    return this.http
      .get<string>(`${this.API_RO_URL}/ros/document/${id}`)
  }


  public getRdfPublicServices(
    page: number,
    rows: number,
    searchTerm: string,
    filterTag: string,
    filterType: string,
    sortBy: string,
    website: string,
    rdfFilters: Map<string, Array<string>>
  ): Observable<PublicServiceResults> {

    const rdfFiltersMap = {};
    rdfFilters.forEach((val: string[], key: string) => {
      rdfFiltersMap[key] = val;
    });

    var pageQuery = '?page=' + page;
    if (rows > 0) {
      pageQuery = pageQuery + '&rows=' + rows;
    }
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
    if (website) {
      pageQuery = pageQuery + '&website=' + website;
    }
    return this.http.post<PublicServiceResults>(`${this.API_CPSV_URL}/rdf_public_services${pageQuery}`, {
      rdfFilters: rdfFiltersMap
    });
  }


  public getRdfContactPoints(
    page: number,
    rows: number,
    searchTerm: string,
    filterTag: string,
    filterType: string,
    sortBy: string,
    website: string,
    rdfFilters: Map<string, Array<string>>
  ): Observable<ContactPointResults> {

    const rdfFiltersMap = {};
    rdfFilters.forEach((val: string[], key: string) => {
      rdfFiltersMap[key] = val;
    });

    var pageQuery = '?page=' + page;
    if (rows > 0) {
      pageQuery = pageQuery + '&rows=' + rows;
    }
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
    if (website) {
      pageQuery = pageQuery + '&website=' + website;
    }
    return this.http.post<ContactPointResults>(`${this.API_CPSV_URL}/rdf_contact_points${pageQuery}`, {
      rdfFilters: rdfFiltersMap
    });
  }

  public getPs(id: string): Observable<PublicService> {
    return this.http
      .get<PublicService>(`${this.API_CPSV_URL}/ps/${id}`)
      .pipe(map((item) => this.psAdapter.adapt(item)));
  }

  public getCp(id: string): Observable<ContactPoint> {
    return this.http
      .get<ContactPoint>(`${this.API_CPSV_URL}/cp/${id}`)
      .pipe(map((item) => this.cpAdapter.adapt(item)));
  }

  public fetchDropdowns(
    typename: string,
  ): Observable<RdfFilter[]> {
    return this.http.get<RdfFilter[]>(
      `${this.API_CPSV_URL}/${typename}/entity_map`
    )
  }

  public rdf_get_name_of_entity(typeName, entity) {
    let entities = []

    if (typeName === 'ps') {
      entities = [
        {value: 'http://www.w3.org/ns/dcat#hasContactPoint', name: 'Contact Point'},
        {value: 'http://data.europa.eu/m8g/hasCompetentAuthority', name: 'Competent Authority'},
        {value: 'http://purl.org/vocab/cpsv#isClassifiedBy', name: 'Related Concept'},
        {value: 'http://cefat4cities.com/public_services/hasBusinessEvent', name: 'Business Event'},
        {value: 'http://cefat4cities.com/public_services/hasLifeEvent', name: 'Life Event'},
      ]
    } else if (typeName === 'cp') {
      entities = [
        {value: 'http://www.w3.org/ns/dcat#hasContactPoint', name: 'Public Service'},
      ]
    }

    return entities.find(i => i.value === entity).name;
  }

  public fetchDropdownFilters(
    typeName: string,
    uriType: RdfFilter,
    keyword: string,
    rdfFilters: Map<string, Array<string>>,
  ): Observable<string[]> {

    const rdfFiltersMap = {};
    rdfFilters.forEach((val: string[], key: string) => {
      rdfFiltersMap[key] = val;
    });

    return this.http.post<string[]>(`${this.API_CPSV_URL}/${typeName}/dropdown_options`, {
      uri_type: uriType,
      keyword,
      rdfFilters: rdfFiltersMap,
    });
  }

}
