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
  selector: 'app-ro-list',
  templateUrl: './ro-list.component.html',
  styleUrls: ['./ro-list.component.css'],
})
export class RoListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;
  ros: ReportingObligation[];
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

  constructor(private service: ApiService) {}

  ngOnInit() {
    this.fetchRos();
    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.page = 1;
        this.fetchRos();
      });
  }

  fetchRos() {
    this.service
      .getRos(
        this.page,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.sortBy
      )
      .subscribe((results) => {
        this.ros = results.results;
        this.collectionSize = results.count;
      });
  }

  onSearch(keyword: string) {
    this.searchTermChanged.next(keyword);
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
}