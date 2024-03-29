import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { debounceTime, switchMap, tap } from 'rxjs/operators';
import { DocumentResults } from 'src/app/shared/models/document';
import { Environment } from 'src/environments/environment-variables';

interface State {
  page: number;
  searchTerm: string;
  filterType: string;
  username: string;
  website: string;
  showOnlyOwn: boolean;
  bookmarks: boolean;
  filterTag: string;
  sortBy: string;
  celex: string;
  type: string;
  status: string;
  eli: string;
  author: string;
  date_of_effect: string;
}

@Injectable({
  providedIn: 'root',
})
export class DocumentService {
  API_URL = Environment.ANGULAR_DJANGO_API_URL;

  private _loading$ = new BehaviorSubject<boolean>(true);
  private _search$ = new Subject<void>();
  private _documentResults$ = new BehaviorSubject<DocumentResults>(null);
  private _total$ = new BehaviorSubject<number>(0);

  private _state: State = {
    page: 1,
    searchTerm: '',
    filterType: '',
    username: '',
    website: '',
    showOnlyOwn: false,
    bookmarks: false,
    filterTag: '',
    sortBy: '-date',
    celex: '',
    type: '',
    status: '',
    eli: '',
    author: '',
    date_of_effect: '',
  };

  constructor(private http: HttpClient) {
    this._search$
      .pipe(
        tap(() => this._loading$.next(true)),
        debounceTime(600),
        switchMap(() => this._search()),
        tap(() => this._loading$.next(false))
      )
      .subscribe((result) => {
        this._documentResults$.next(result);
        this._total$.next(result.count);
      });

    this._search$.next();
  }

  get documentResults$() {
    return this._documentResults$.asObservable();
  }
  get total$() {
    return this._total$.asObservable();
  }
  get loading$() {
    return this._loading$.asObservable();
  }
  get page() {
    return this._state.page;
  }
  set page(page: number) {
    this._set({ page });
  }
  get searchTerm() {
    return this._state.searchTerm;
  }
  set searchTerm(searchTerm: string) {
    this._set({ searchTerm });
  }
  get filterType() {
    return this._state.filterType;
  }
  set filterType(filterType: string) {
    this._set({ filterType });
  }
  get username() {
    return this._state.username;
  }
  set username(username: string) {
    this._set({ username });
  }
  get website() {
    return this._state.website;
  }
  set website(website: string) {
    this._set({ website });
  }
  get showOnlyOwn() {
    return this._state.showOnlyOwn;
  }
  set showOnlyOwn(showOnlyOwn: boolean) {
    this._set({ showOnlyOwn });
  }
  get bookmarks() {
    return this._state.bookmarks;
  }
  set bookmarks(bookmarks: boolean) {
    this._set({ bookmarks });
  }
  get celex() {
    return this._state.celex;
  }
  set celex(celex: string) {
    this._set({ celex });
  }
  get type() {
    return this._state.type;
  }
  set type(type: string) {
    this._set({ type });
  }
  get status() {
    return this._state.status;
  }
  set status(status: string) {
    this._set({ status });
  }
  get eli() {
    return this._state.eli;
  }
  set eli(eli: string) {
    this._set({ eli });
  }
  get author() {
    return this._state.author;
  }
  set author(author: string) {
    this._set({ author });
  }
  get date_of_effect() {
    return this._state.date_of_effect;
  }
  set date_of_effect(date_of_effect: string) {
    this._set({ date_of_effect });
  }
  get filterTag() {
    return this._state.searchTerm;
  }
  set filterTag(filterTag: string) {
    this._set({ filterTag });
  }

  set sortBy(sortBy: string) {
    this._set({ sortBy });
  }

  private _set(patch: Partial<State>) {
    Object.assign(this._state, patch);
    this._search$.next();
  }

  private _search(): Observable<DocumentResults> {
    const {
      page,
      searchTerm,
      filterType,
      username,
      website,
      showOnlyOwn,
      bookmarks,
      celex,
      type,
      status,
      eli,
      author,
      date_of_effect,
      filterTag,
      sortBy,
    } = this._state;
    const pageQuery =
      '?page=' +
      page +
      '&keyword=' +
      searchTerm +
      '&filterType=' +
      filterType +
      '&username=' +
      username +
      '&website=' +
      website +
      '&showOnlyOwn=' +
      showOnlyOwn +
      '&bookmarks=' +
      bookmarks +
      '&celex=' +
      celex +
      '&type=' +
      type +
      '&status=' +
      status +
      '&eli=' +
      eli +
      '&author=' +
      author +
      '&date_of_effect=' +
      date_of_effect +
      '&tag=' +
      filterTag +
      '&ordering=' +
      sortBy;
    return this.http.get<DocumentResults>(
      `${this.API_URL}/documents${pageQuery}`
    );
  }

  public total_documents(): Observable<number> {
    return this.http.get<number>(
      `${this.API_URL}/stats/total_documents`
    );
  }
}
