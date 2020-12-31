import {
  Component,
  OnInit,
  Directive,
  Input,
  Output,
  EventEmitter,
  ViewChildren,
  QueryList,
} from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { Concept } from 'src/app/shared/models/concept';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {
  faUserAlt,
  faMicrochip,
  faSyncAlt,
  faStopCircle,
  faSort,
  faSortUp,
  faSortDown,
} from '@fortawesome/free-solid-svg-icons';
import { Subject } from 'rxjs';
import { ConceptTag } from 'src/app/shared/models/ConceptTag';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import {Router} from "@angular/router";
import {DjangoUser} from "../../shared/models/django_user";
import {AuthenticationService} from "../../core/auth/authentication.service";

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

declare const annotator: any;

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
  selector: 'app-concept-list',
  templateUrl: './concept-list.component.html',
  styleUrls: ['./concept-list.component.css'],
})
export class ConceptListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;
  concepts: Concept[];
  collectionSize = 0;
  selectedIndex: string = null;
  page = 1;
  previousPage: any;
  pageSize = 5;
  keyword = '';
  filterTag = '';
  sortBy = 'name';
  filterType = '';
  version = '8a4f1d58';
  website = '';
  searchTermChanged: Subject<string> = new Subject<string>();
  userIcon: IconDefinition = faUserAlt;
  chipIcon: IconDefinition = faMicrochip;
  reloadIcon: IconDefinition = faSyncAlt;
  resetIcon: IconDefinition = faStopCircle;
  nameSortIcon: IconDefinition = faSort;
  dateSortIcon: IconDefinition = faSortDown;
  statesSortIcon: IconDefinition = faSort;
  currentDjangoUser: DjangoUser;
  filters = [
    { id: '', name: 'Filter..' },
    { id: 'unvalidated', name: '..Unvalidated' },
    { id: 'accepted', name: '..Accepted' },
    { id: 'rejected', name: '..Rejected' },
  ];
  versions = [{ id: '', name: 'Version...'}]
  websites = [ { id: '', name: 'Website..' } ];

  constructor(
    private service: ApiService,
    private router: Router,
    private authenticationService: AuthenticationService,
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );

    // Force login page when not authenticated
    if (this.currentDjangoUser == null) {
      this.router.navigate(['/login']);
    }

    this.fetchVersions();
    this.fetchConcepts();
    this.fetchWebsites();

    this.service.messageSource.asObservable().subscribe((value: string) => {
      if (value === 'refresh') {
        this.fetchConcepts();
      }
    });

    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.page = 1;
        this.fetchConcepts();
      });
  }

  fetchConcepts() {
    this.service
      .getConcepts(
        this.page,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.version,
        this.website,
        this.sortBy
      )
      .subscribe((results) => {
        this.concepts = results.results;
        this.collectionSize = results.count;
      });
  }

  fetchVersions() {
    this.service
      .getConceptVersions()
      .subscribe((versions) => {
        versions.forEach((version) =>{
          this.versions.push({id: version, name: '..' + version });
        })
      });
  }
  fetchWebsites() {
    this.service.getWebsites().subscribe((websites) => {
      websites.forEach((website) => {
        this.websites.push({
          id: website.name.toLowerCase(),
          name: '..' + website.name.toUpperCase(),
        });
      });
    });
  }

  onSearch(keyword: string) {
    this.searchTermChanged.next(keyword);
  }

  loadPage(page: number) {
    if (page !== this.previousPage) {
      this.page = page;
      this.previousPage = page;
      this.fetchConcepts();
    }
  }

  onPageChange() {
    this.router.navigate(['/glossary']);
  }

  filterResetPage() {
    this.page = 1;
    this.fetchConcepts();
    this.router.navigate(['/glossary']);
  }

  setIndex(index: string) {
    this.selectedIndex = index;
  }

  onSort({ column, direction }: SortEvent) {
    console.log('sort(' + column + '/' + direction + ')');
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting documents, default date descending (-date)
    if (direction === '') {
      this.sortBy = 'name';
      this.nameSortIcon = faSort;
      this.dateSortIcon = faSortDown;
      this.statesSortIcon = faSort;
      this.fetchConcepts();
    } else {
      this.sortBy = direction === 'asc' ? '' : '-';
      if (column === 'states') {
        column = 'acceptance_state_max_probability';
      }
      this.sortBy += column;
      const sortIcon = direction === 'asc' ? faSortUp : faSortDown;
      if (column === 'name') {
        this.nameSortIcon = sortIcon;
        this.dateSortIcon = faSort;
        this.statesSortIcon = faSort;
      } else if (column === 'date') {
        this.dateSortIcon = sortIcon;
        this.nameSortIcon = faSort;
        this.statesSortIcon = faSort;
      } else {
        this.statesSortIcon = sortIcon;
        this.nameSortIcon = faSort;
        this.dateSortIcon = faSort;
      }
      this.fetchConcepts();
    }
  }

  onAddTag(event, tags, conceptId) {
    const newTag = new ConceptTag('', event.value, conceptId);
    this.service.addConceptTag(newTag).subscribe((addedTag) => {
      // primeng automatically adds the string value first, delete this as workaround
      // see: https://github.com/primefaces/primeng/issues/3419
      tags.splice(-1, 1);
      // now add the tag object
      tags.push(addedTag);
    });
  }

  onRemoveTag(event) {
    this.service.deleteConceptTag(event.value.id).subscribe();
  }

  onClickTag(event) {
    this.filterTag = event.value.value;
    this.fetchConcepts();
  }
}
