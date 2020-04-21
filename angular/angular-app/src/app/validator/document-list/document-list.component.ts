import { Observable } from 'rxjs';
import { switchMap, distinctUntilChanged, debounceTime } from 'rxjs/operators';
import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { Document, DocumentResults } from 'src/app/shared/models/document';
import { Subject } from 'rxjs';
import { Tag } from 'src/app/shared/models/tag';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faUserAlt } from '@fortawesome/free-solid-svg-icons';
import { DjangoUser } from 'src/app/shared/models/django_user';
import { AuthenticationService } from 'src/app/core/auth/authentication.service';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css'],
})
export class DocumentListComponent implements OnInit {
  documents$: Document[];
  documentsResults$: Observable<DocumentResults>;
  selectedId: number;
  page: any = 1;
  previousPage: any;
  pageSize = 5;
  stats = {
    unValidatedSize: 0,
    unValidatedPercent: 0,
    autoValidatedSize: 0,
    autoValidatedPercent: 0,
    autoRejectedSize: 0,
    autoRejectedPercent: 0,
    autoRejectedSizeCSS: 'width: 30%',
    humanRejectedSize: 0,
    humanRejectedPercent: 0,
    humanAcceptedSize: 0,
    humanAcceptedPercent: 0,
  };
  collectionSize = 0;
  filterType: string = 'none';
  keyword: string;
  userIcon: IconDefinition;
  filters = [
    { id: 'none', name: 'Filter..' },
    { id: 'own', name: '..Validated by me' },
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

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService,
    private authenticationService: AuthenticationService
  ) {}

  fetchDocuments() {
    console.log(this.filterType);
    this.service
      .getDocumentResults(
        this.page,
        this.keyword,
        this.filterType,
        this.currentDjangoUser.username,
        this.websiteFilter
      )
      .subscribe((result) => {
        this.documents$ = result.results;
        this.collectionSize = result.count;
      });
  }
  ngOnInit() {
    this.userIcon = faUserAlt;
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

  loadPage(page: number) {
    if (page !== this.previousPage) {
      this.page = page;
      this.previousPage = page;
      this.fetchDocuments();
    }
  }
}
