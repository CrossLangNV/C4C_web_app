import {
  Component,
  OnInit,
  Directive,
  EventEmitter,
  Input,
  Output,
  QueryList,
  ViewChildren,
} from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { SolrFile } from '../../shared/models/solrfile';
import { ApiService } from '../../core/services/api.service';

export type SortDirection = 'asc' | 'desc' | '';
const rotate: { [key: string]: SortDirection } = {
  asc: 'desc',
  desc: '',
  '': 'asc',
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
  selector: 'app-solrfile-list',
  templateUrl: './solrfile-list.component.html',
  styleUrls: ['./solrfile-list.component.css'],
})
export class SolrFileListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;

  page = 1;
  previousPage = 0;
  pageSize = 10;
  cachedSolrFilesBeforeSort = [];
  cachedSolrFiles = [];
  searchTerm = '';
  searchTermChanged: Subject<string> = new Subject<string>();
  collectionSize = 0;

  constructor(private apiService: ApiService) {}

  fetchSolrFiles(searchTerm) {
    if (searchTerm === '') {
      this.apiService
        .getSolrFiles(this.page, this.pageSize)
        .subscribe((data) => {
          this.collectionSize = data[0];
          this.cachedSolrFilesBeforeSort = data[1] as SolrFile[];
          this.cachedSolrFilesBeforeSort.forEach((file) => {
            this.apiService
              .getDocument(file.documentId)
              .subscribe((document) => {
                file.website = document.website;
                file.documentTitle = document.title;
              });
          });
          this.cachedSolrFiles = [...this.cachedSolrFilesBeforeSort];
        });
    } else {
      this.apiService
        .searchSolrFiles(this.page, this.pageSize, this.searchTerm)
        .subscribe((data) => {
          this.collectionSize = data[0];
          this.cachedSolrFilesBeforeSort = data[1] as SolrFile[];
          this.cachedSolrFilesBeforeSort.forEach((file) => {
            this.apiService
              .getDocument(file.documentId)
              .subscribe((document) => {
                file.website = document.website;
                file.documentTitle = document.title;
              });
          });
          this.cachedSolrFiles = [...this.cachedSolrFilesBeforeSort];
        });
    }
  }

  ngOnInit() {
    this.fetchSolrFiles('');
    this.searchTermChanged
      .pipe(debounceTime(200), distinctUntilChanged())
      .subscribe((model) => {
        this.searchTerm = model;
        this.fetchSolrFiles(this.searchTerm);
      });
  }

  get files(): SolrFile[] {
    return this.cachedSolrFiles;
  }

  set files(files: SolrFile[]) {
    this.files = files;
  }

  loadPage(page: number) {
    if (page !== this.previousPage) {
      this.page = page;
      this.previousPage = page;
      this.fetchSolrFiles(this.searchTerm);
    }
  }

  onSearch(searchTerm: string) {
    this.searchTermChanged.next(searchTerm);
  }

  onSort({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting files
    if (direction === '') {
      this.cachedSolrFiles = [...this.cachedSolrFilesBeforeSort];
    } else {
      this.cachedSolrFiles = this.cachedSolrFiles.sort((a, b) => {
        const res = compare(a[column], b[column]);
        return direction === 'asc' ? res : -res;
      });
    }
  }
}
