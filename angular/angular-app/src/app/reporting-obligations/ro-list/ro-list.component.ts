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
import {Router} from "@angular/router";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {DjangoUser} from "../../shared/models/django_user";

import {SelectItem} from "primeng/api";
import {logger} from "codelyzer/util/logger";

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

  // RO Splits
  reporters: SelectItem[] = [];
  selectedReporter: RoDetail;
  verbs: SelectItem[] = [];
  selectedVerb: RoDetail;
  reports: SelectItem[] = [];
  selectedReport: RoDetail
  regulatoryBodies: SelectItem[] = [];
  selectedRegulatoryBody: RoDetail
  propMods: SelectItem[] = [];
  selectedPropMod: RoDetail
  entities: SelectItem[] = [];
  selectedEntity: RoDetail
  frequencies: SelectItem[] = [];
  selectedFrequency: RoDetail

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

    this.fetchRos();
    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.page = 1;
        this.fetchRos();
      });

    // Fetch RDF for filters
    this.fetchReporters();
    this.fetchVerbs();
    this.fetchReports();
    this.fetchRegulatoryBodies();
    this.fetchPropMods();
    this.fetchEntities();
    this.fetchFrequencies();
  }

  fetchReporters() {
    this.service
      .fetchReporters(
      )
      .subscribe((results) => {
        results.forEach((reporter) => {
          this.reporters.push({ label: reporter, value: reporter });
        });
    })
  }

  fetchVerbs() {
    this.service
      .fetchVerbs(
      )
      .subscribe((results) => {
        results.forEach((verb) => {
          this.verbs.push({ label: verb, value: verb });
        });
      })
  }

  // Fetch Reports
  fetchReports() {
    this.service
      .fetchReports(
      )
      .subscribe((results) => {
        results.forEach((report) => {
          this.reports.push({ label: report, value: report });
        });
      })
  }
  // Fetch regulatoryBodies
  fetchRegulatoryBodies() {
    this.service
      .fetchRegulatoryBody(
      )
      .subscribe((results) => {
        results.forEach((regulatorybody) => {
          this.regulatoryBodies.push({ label: regulatorybody, value: regulatorybody });
        });
      })
  }
  // Fetch propMods
  fetchPropMods() {
    this.service
      .fetchPropMod(
      )
      .subscribe((results) => {
        results.forEach((propmod) => {
          this.propMods.push({ label: propmod, value: propmod });
        });
      })
  }
  // Fetch entities
  fetchEntities() {
    this.service
      .fetchEntity(
      )
      .subscribe((results) => {
        results.forEach((entity) => {
          this.entities.push({ label: entity, value: entity });
        });
      })
  }
  // Fetch frequencies
  fetchFrequencies() {
    this.service
      .fetchFrequency(
      )
      .subscribe((results) => {
        results.forEach((frequency) => {
          this.frequencies.push({ label: frequency, value: frequency });
        });
      })
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

  getRoQueryString(): string {
    let reporter = this.selectedReporter.name
    let verb = this.selectedVerb.name
    let report = this.selectedReport.name
    let regBody = this.selectedRegulatoryBody.name
    let propMod = this.selectedPropMod.name
    let entity = this.selectedEntity.name
    let frequency = this.selectedFrequency.name

    let array = [reporter, verb, report, regBody, propMod, entity, frequency]

    return array.join(" ")
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
    this.selectedReporter = null
    this.selectedVerb = null
    this.selectedReport = null
    this.selectedRegulatoryBody = null
    this.selectedPropMod = null
    this.selectedEntity = null
    this.selectedFrequency = null
  }
}
