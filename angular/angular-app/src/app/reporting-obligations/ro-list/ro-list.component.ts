import {
  Component,
  OnInit,
  Directive,
  Input,
  Output,
  EventEmitter,
  ViewChildren,
  QueryList, ViewChild,
} from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { ReportingObligation } from 'src/app/shared/models/ro';
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
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import {Router} from "@angular/router";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {DjangoUser} from "../../shared/models/django_user";

import {RdfFilter} from "../../shared/models/rdfFilter";

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

export interface RoDetail {
  name: string;
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
  selector: 'app-ro-list',
  templateUrl: './ro-list.component.html',
  styleUrls: ['./ro-list.component.css'],
})
export class RoListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;
  ros: ReportingObligation[];

  availableItems: RdfFilter[]
  availableItemsKeys: []
  availableItemsQuery: Map<string, string>;

  selected: string;
  collectionSize = 0;
  selectedIndex: string = null;
  page = 1;
  previousPage: any;
  pageSize = 5;
  keyword = '';
  filterTag = '';
  sortBy = 'name';
  filterType = 'none';
  searchTermChanged: Subject<string> = new Subject<string>();
  userIcon: IconDefinition = faUserAlt;
  chipIcon: IconDefinition = faMicrochip;
  reloadIcon: IconDefinition = faSyncAlt;
  resetIcon: IconDefinition = faStopCircle;
  nameSortIcon: IconDefinition = faSort;
  dateSortIcon: IconDefinition = faSortDown;
  statesSortIcon: IconDefinition = faSort;
  currentDjangoUser: DjangoUser;

  collapsed: boolean = true;

  constructor(
    private service: ApiService,
    private router: Router,
    private authenticationService: AuthenticationService,
  ) {}

  ngOnInit() {
    this.availableItemsQuery = new Map<string, string>();

    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );

    // Force login page when not authenticated
    if (this.currentDjangoUser == null) {
      this.router.navigate(['/login']);
    }

    // Fetch RDF for filters
    this.fetchAvailableFilters();

    this.fetchRos();
    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.page = 1;
        this.fetchRos();
      });
  }

  fetchAvailableFilters() {
    this.service
      .fetchDropdowns()
      .subscribe((results) => {
          this.availableItems = results
      })
  }

  fetchRos() {
    this.service
      .getRdfRos(
        this.page,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.sortBy,
        this.availableItemsQuery
      )
      .subscribe((results) => {
        this.ros = results.results;
        this.collectionSize = results.count;
      });
  }

  /*onSearch(filter, keyword: string) {
    this.searchTermChanged.next(keyword);
  }*/

  onQuery(filter, keyword) {
    if (keyword.code == "") {
      this.availableItemsQuery.delete(filter.entity)
    } else {
      this.availableItemsQuery.set(filter.entity, keyword.name)
    }
    this.filterResetPage();
  }

  loadPage(page: number) {
    if (page !== this.previousPage) {
      this.page = page;
      this.previousPage = page;
      this.fetchRos();
    }
  }

  filterResetPage() {
    this.page = 1;
    this.fetchRos();
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
      this.fetchRos();
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
      this.fetchRos();
    }
  }

  onClickTag(event) {
    this.filterTag = event.value.value;
    this.fetchRos();
  }

  resetFilters() {
    this.availableItems = [];
    this.availableItemsQuery.clear();
    this.fetchAvailableFilters();
    this.fetchRos();
  }

  collapsePanel() {
    if (this.collapsed == true) {
      this.collapsed = false;
    } else {
      this.collapsed = true;
    }
  }
}
