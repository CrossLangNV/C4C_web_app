import {
  Component,
  OnInit,
  Directive,
  EventEmitter,
  Input,
  Output,
  QueryList,
  ViewChildren
} from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ApiServiceWebsites } from '../../core/services/api.service.websites';
import { Website } from '../../shared/models/website';

export type SortDirection = 'asc' | 'desc' | '';
const rotate: { [key: string]: SortDirection } = {
  asc: 'desc',
  desc: '',
  '': 'asc'
};

export const compare = (v1, v2) => {
  if (v1 === v2) {
    return 0;
  } else if (v1 === null || v1 === undefined) {
    return 1;
  } else if (v2 === null || v2 === undefined) {
    return -1;
  } else {
    return v1 < v2 ? -1 : 1;
  }
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
    '(click)': 'rotate()'
  }
})

export class WebsiteNgbdSortableHeaderDirective {
  @Input() sortable: string;
  @Input() direction: SortDirection = '';
  @Output() sort = new EventEmitter<SortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.sort.emit({ column: this.sortable, direction: this.direction });
  }
}

@Component({
  selector: 'app-website-list',
  templateUrl: './website-list.component.html',
  styleUrls: ['./website-list.component.css']
})
export class WebsiteListComponent implements OnInit {
  @ViewChildren(WebsiteNgbdSortableHeaderDirective) headers: QueryList<
    WebsiteNgbdSortableHeaderDirective
  >;

  page = 1;
  pageSize = 10;
  cachedWebsitesBeforeSort = [];
  cachedWebsites = [];
  searchTerm = '';
  searchTermChanged: Subject<string> = new Subject<string>();
  collectionSize = 0;

  constructor(private apiServiceWebsites: ApiServiceWebsites) {}

  ngOnInit() {
    this.apiServiceWebsites.getWebsites().subscribe(websites => {
      this.cachedWebsitesBeforeSort = websites as Website[];
      this.cachedWebsites = [...this.cachedWebsitesBeforeSort];
      this.collectionSize = this.cachedWebsites.length;
    });
    this.searchTermChanged
      .pipe(debounceTime(200), distinctUntilChanged())
      .subscribe(model => {
        this.searchTerm = model;
        this.apiServiceWebsites.searchWebsites(this.searchTerm).subscribe(websites => {
          this.cachedWebsitesBeforeSort = websites as Website[];
          this.cachedWebsites = [...this.cachedWebsitesBeforeSort];
          this.collectionSize = this.cachedWebsites.length;
        });
      });
  }

  get websites(): Website[] {
    return this.cachedWebsites.slice(
      (this.page - 1) * this.pageSize,
      (this.page - 1) * this.pageSize + this.pageSize
    );
  }

  set websites(websites: Website[]) {
    this.websites = websites;
  }

  onSearch(searchTerm: string) {
    this.searchTermChanged.next(searchTerm);
  }

  onSort({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting websites
    if (direction === '') {
      this.cachedWebsites = [...this.cachedWebsitesBeforeSort];
    } else {
      this.cachedWebsites = this.cachedWebsites.sort((a, b) => {
        const res = compare(a[column], b[column]);
        return direction === 'asc' ? res : -res;
      });
    }
  }

  onDelete(id) {
    this.apiServiceWebsites.deleteWebsite(id).subscribe(
    );
  }

}
