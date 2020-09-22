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
  email: string;
  website: string;
  showOnlyOwn: boolean;
  filterTag: string;
  sortBy: string;
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
    email: '',
    website: '',
    showOnlyOwn: false,
    filterTag: '',
    sortBy: '-date',
  };

  constructor(private http: HttpClient) {
    this._search$
      .pipe(
        tap(() => this._loading$.next(true)),
        debounceTime(200),
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
  get email() {
    return this._state.email;
  }
  set email(email: string) {
    this._set({ email });
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
      email,
      website,
      showOnlyOwn,
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
      '&email=' +
      email +
      '&website=' +
      website +
      '&showOnlyOwn=' +
      showOnlyOwn +
      '&tag=' +
      filterTag +
      '&ordering=' +
      sortBy;
    return this.http.get<DocumentResults>(
      `${this.API_URL}/documents${pageQuery}`
    );
  }
}
