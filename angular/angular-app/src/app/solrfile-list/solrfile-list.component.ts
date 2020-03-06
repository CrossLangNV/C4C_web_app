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
import { SolrFile } from '../solrfile';
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
  selector: 'app-solrfile-list',
  templateUrl: './solrfile-list.component.html',
  styleUrls: ['./solrfile-list.component.css']
})
export class SolrFileListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;

  page = 1;
  pageSize = 10;
  cachedSolrFilesBeforeSort = [];
  cachedSolrFiles = [];
  searchTerm = '';
  searchTermChanged: Subject<string> = new Subject<string>();
  collectionSize = 0;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.apiService.getSolrFiles().subscribe(files => {
      this.cachedSolrFilesBeforeSort = files as SolrFile[];
      this.cachedSolrFilesBeforeSort.forEach(file => {
        this.apiService.getAttachment(file.id).subscribe(attachment => {
          file.rawFile = attachment.file;
        });
        this.apiService.getDocument(file.documentId).subscribe(document => {
          file.documentTitle = document.title;
          this.apiService.getWebsite(document.website).subscribe(website => {
            file.website = website.name;
          });
        });
      });
      this.cachedSolrFiles = [...this.cachedSolrFilesBeforeSort];
      this.collectionSize = this.cachedSolrFiles.length;
    });
    this.searchTermChanged
      .pipe(debounceTime(200), distinctUntilChanged())
      .subscribe(model => {
        this.searchTerm = model;
        this.apiService.searchSolrFiles(this.searchTerm).subscribe(files => {
          this.cachedSolrFilesBeforeSort = files as SolrFile[];
          this.cachedSolrFilesBeforeSort.forEach(file => {
            this.apiService.getAttachment(file.id).subscribe(attachment => {
              file.rawFile = attachment.file;
            });
            this.apiService.getDocument(file.documentId).subscribe(document => {
              file.documentTitle = document.title;
              this.apiService
                .getWebsite(document.website)
                .subscribe(website => {
                  file.website = website.name;
                });
            });
          });
          this.cachedSolrFiles = [...this.cachedSolrFilesBeforeSort];
          this.collectionSize = this.cachedSolrFiles.length;
        });
      });
  }

  get files(): SolrFile[] {
    return this.cachedSolrFiles.slice(
      (this.page - 1) * this.pageSize,
      (this.page - 1) * this.pageSize + this.pageSize
    );
  }

  set files(files: SolrFile[]) {
    this.files = files;
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
