import { Observable } from 'rxjs';
import { switchMap, distinctUntilChanged, debounceTime } from 'rxjs/operators';
import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { Document, DocumentResults } from 'src/app/shared/models/document';
import { Subject } from 'rxjs';
import { Tag } from 'src/app/shared/models/tag';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {
  faUserAlt,
  faMicrochip,
  faSyncAlt,
  faStopCircle,
} from '@fortawesome/free-solid-svg-icons';
import { DjangoUser } from 'src/app/shared/models/django_user';
import { AuthenticationService } from 'src/app/core/auth/authentication.service';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css'],
})
export class DocumentListComponent implements OnInit {
  documents$: Document[];
  selectedId: number;
  page: any = 1;
  previousPage: any;
  pageSize = 5;
  showOnlyOwn: boolean = false;
  filterActive: boolean = false;
  stats = {
    total: 0,
    unValidatedSize: 0,
    validatedSize: 0,
    validatedPercent: 0,
    unValidatedPercent: 0,
    autoValidatedSize: 0,
    autoValidatedPercent: 0,
    autoRejectedSize: 0,
    autoRejectedPercent: 0,
    humanRejectedSize: 0,
    humanRejectedPercent: 0,
    humanAcceptedSize: 0,
    humanAcceptedPercent: 0,
  };
  collectionSize = 0;
  filterType: string = 'none';
  filterTag: string = '';
  keyword: string = '';
  userIcon: IconDefinition;
  chipIcon: IconDefinition;
  reloadIcon: IconDefinition = faSyncAlt;
  resetIcon: IconDefinition = faStopCircle;
  filters = [
    { id: 'none', name: 'Filter..' },
    { id: 'unvalidated', name: '..Unvalidated' },
    { id: 'accepted', name: '..Accepted' },
    { id: 'rejected', name: '..Rejected' },
  ];
  websites = [
    { id: 'none', name: 'Website..' },
    { id: 'bis', name: '..BIS' },
    { id: 'eiopa', name: '..EIOPA' },
    { id: 'esma', name: '..ESMA' },
    { id: 'eurlex', name: '..EURLEX' },
    { id: 'fsb', name: '..FSB' },
    { id: 'srb', name: '..SRB' },
    { id: 'eba', name: '..EBA' },
  ];
  websiteFilter: string = 'none';
  searchTermChanged: Subject<string> = new Subject<string>();
  currentDjangoUser: DjangoUser;
  selectedIndex: string = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService,
    private authenticationService: AuthenticationService
  ) {}

  fetchDocuments() {
    this.checkFilters();
    // Fetch documents list
    this.service
      .getDocumentResults(
        this.page,
        this.keyword,
        this.filterType,
        this.currentDjangoUser.username,
        this.websiteFilter,
        this.showOnlyOwn,
        this.filterTag
      )
      .subscribe((result) => {
        this.documents$ = result.results;
        this.collectionSize = result.count;
      });
    // Fetch statistics
    this.service.getDocumentStats().subscribe((result) => {
      this.stats.total = result.count_total;
      this.stats.validatedSize = result.count_total - result.count_unvalidated;
      this.stats.validatedPercent = Math.round(
        (this.stats.validatedSize / result.count_total) * 100
      );
      this.stats.unValidatedSize = result.count_unvalidated;
      this.stats.humanRejectedSize = result.count_rejected;
      this.stats.humanAcceptedSize = result.count_validated;
      this.stats.autoRejectedSize = result.count_autorejected;
      this.stats.autoValidatedSize = result.count_autovalidated;
    });
  }
  ngOnInit() {
    this.userIcon = faUserAlt;
    this.chipIcon = faMicrochip;
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );
    this.fetchDocuments();
    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.fetchDocuments();
      });
    this.service.messageSource.asObservable().subscribe((value: string) => {
      if (value == 'refresh') {
        this.fetchDocuments();
      }
    });
  }

  onSearch(keyword: string) {
    this.searchTermChanged.next(keyword);
  }

  onAddTag(event, tags, documentId) {
    const newTag = new Tag('', event.value, documentId);
    this.service.addTag(newTag).subscribe((addedTag) => {
      // primeng automatically adds the string value first, delete this as workaround
      // see: https://github.com/primefaces/primeng/issues/3419
      tags.splice(-1, 1);
      // now add the tag object
      tags.push(addedTag);
    });
  }

  onRemoveTag(event) {
    this.service.deleteTag(event.value.id).subscribe();
  }

  onClickTag(event) {
    this.filterTag = event.value.value;
    this.fetchDocuments();
  }

  loadPage(page: number) {
    if (page !== this.previousPage) {
      this.page = page;
      this.previousPage = page;
      this.fetchDocuments();
    }
  }

  filterResetPage() {
    this.page = 1;
    this.fetchDocuments();
  }

  setIndex(index: string) {
    this.selectedIndex = index;
  }

  checkFilters() {
    this.filterActive =
      this.keyword.length > 0 ||
      this.filterTag.length > 0 ||
      this.showOnlyOwn ||
      this.filterType != 'none' ||
      this.websiteFilter != 'none';
  }

  resetFilters() {
    this.keyword = '';
    this.filterTag = '';
    this.showOnlyOwn = false;
    this.filterType = 'none';
    this.websiteFilter = 'none';
    this.fetchDocuments();
  }
}
