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
import { Film } from '../film';
import { ApiService } from '../api.service';

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
  selector: 'app-film-list',
  templateUrl: './film-list.component.html',
  styleUrls: ['./film-list.component.css']
})
export class FilmListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;

  page = 1;
  pageSize = 50;
  cachedFilmsBeforeSort = [];
  cachedFilms = [];
  searchTerm = '';
  searchTermChanged: Subject<string> = new Subject<string>();
  collectionSize = 0;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.apiService.getFilms().subscribe(films => {
      this.cachedFilmsBeforeSort = films as Film[];
      this.cachedFilms = [...this.cachedFilmsBeforeSort];
      this.collectionSize = this.cachedFilms.length;
    });
    this.searchTermChanged
      .pipe(debounceTime(200), distinctUntilChanged())
      .subscribe(model => {
        this.searchTerm = model;
        this.apiService.searchFilms(this.searchTerm).subscribe(films => {
          this.cachedFilmsBeforeSort = films as Film[];
          this.cachedFilms = [...this.cachedFilmsBeforeSort];
          this.collectionSize = this.cachedFilms.length;
        });
      });
  }

  get films(): Film[] {
    return this.cachedFilms.slice(
      (this.page - 1) * this.pageSize,
      (this.page - 1) * this.pageSize + this.pageSize
    );
  }

  set films(films: Film[]) {
    this.films = films;
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

    // sorting films
    if (direction === '') {
      this.cachedFilms = [...this.cachedFilmsBeforeSort];
    } else {
      this.cachedFilms = this.cachedFilms.sort((a, b) => {
        const res = compare(a[column], b[column]);
        return direction === 'asc' ? res : -res;
      });
    }
  }
}
