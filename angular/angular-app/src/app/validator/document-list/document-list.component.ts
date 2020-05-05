import { distinctUntilChanged, debounceTime } from 'rxjs/operators';
import {
  Component,
  OnInit,
  Directive,
  Input,
  Output,
  ViewChildren,
  QueryList,
  EventEmitter,
} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { Document } from 'src/app/shared/models/document';
import { Subject } from 'rxjs';
import { Tag } from 'src/app/shared/models/tag';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {
  faUserAlt,
  faMicrochip,
  faSyncAlt,
  faStopCircle,
  faSort,
  faSortUp,
  faSortDown
} from '@fortawesome/free-solid-svg-icons';
import { DjangoUser } from 'src/app/shared/models/django_user';
import { AuthenticationService } from 'src/app/core/auth/authentication.service';

export type SortDirection = 'asc' | 'desc' | '';
const rotate: { [key: string]: SortDirection } = {
  asc: 'desc',
  desc: '',
  '': 'asc',
};

export interface SortEvent {
  column: string;
  direction: SortDirection;
}

@Directive({
  selector: 'th[sortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()',
  },
})
export class NgbdSortableHeaderDirective {
  @Input() sortable: string;
  @Input() direction: SortDirection = '';
  @Output() sort = new EventEmitter<SortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.sort.emit({ column: this.sortable, direction: this.direction });
  }
}

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css'],
})
export class DocumentListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;

  documents$: Document[];
  selectedId: number;
  page = 1;
  previousPage: any;
  data: any;
  pageSize = 5;
  showOnlyOwn = false;
  filterActive = false;
  stats = {
    total: 0,
    unvalidatedSize: 0,
    unvalidatedPercent: 0,
    validatedSize: 0,
    validatedPercent: 0,
    autoValidatedSize: 0,
    autoValidatedPercent: 0,
    autoRejectedSize: 0,
    autoRejectedPercent: 0,
    rejectedSize: 0,
    rejectedPercent: 0,
    acceptedSize: 0,
    acceptedPercent: 0,
  };
  collectionSize = 0;
  filterType = 'none';
  filterTag = '';
  keyword = '';
  sortBy = '-date';
  userIcon: IconDefinition;
  chipIcon: IconDefinition;
  reloadIcon: IconDefinition = faSyncAlt;
  resetIcon: IconDefinition = faStopCircle;
  titleSortIcon: IconDefinition = faSort;
  dateSortIcon: IconDefinition = faSortDown;
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
  websiteFilter = 'none';
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
        this.filterTag,
        this.sortBy
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
      this.stats.unvalidatedSize = result.count_unvalidated;
      this.stats.unvalidatedPercent = Math.round(
        (this.stats.unvalidatedSize / result.count_total) * 100
      );
      this.stats.acceptedSize = result.count_accepted;
      this.stats.acceptedPercent = Math.round(
        (this.stats.acceptedSize / result.count_total) * 100
      );
      this.stats.rejectedSize = result.count_rejected;
      this.stats.rejectedPercent = Math.round(
        (this.stats.rejectedSize / result.count_total) * 100
      );
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

  onSort({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting documents, default date descending (-date)
    if (direction === '') {
      this.sortBy = '-date';
      this.titleSortIcon = faSort;
      this.dateSortIcon = faSortDown;
      this.fetchDocuments();
    } else {
      this.sortBy = direction === 'asc' ? '' : '-';
      this.sortBy += column;
      const sortIcon = direction === 'asc' ? faSortUp : faSortDown;
      if (column === 'title') {
        this.titleSortIcon = sortIcon;
        this.dateSortIcon = faSort;
      } else {
        this.dateSortIcon = sortIcon;
        this.titleSortIcon = faSort;
      }
      this.fetchDocuments();
    }
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

  updateChart(event: Event) {
    this.data = {
      labels: ['Unvalidated', 'Accepted', 'Rejected'],
      datasets: [
        {
          data: [
            this.stats.unvalidatedPercent,
            this.stats.acceptedPercent,
            this.stats.rejectedPercent,
          ],
          backgroundColor: ['#36A2EB', '#28A745', '#F47677'],
          hoverBackgroundColor: ['#36A2EB', '#28A745', '#F47677'],
        },
      ],
    };
  }
}
