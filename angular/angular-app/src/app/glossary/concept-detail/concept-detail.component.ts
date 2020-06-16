import { Component, OnInit, Directive, Input, Output, EventEmitter, ViewChildren, QueryList } from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { Concept } from 'src/app/shared/models/concept';
import { Document } from 'src/app/shared/models/document';

import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faSort, faSortUp, faSortDown } from '@fortawesome/free-solid-svg-icons';
import { Observable, forkJoin } from 'rxjs';

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
  selector: 'app-concept-detail',
  templateUrl: './concept-detail.component.html',
  styleUrls: ['./concept-detail.component.css'],
})
export class ConceptDetailComponent implements OnInit {
  @ViewChildren(NgbdSortableHeaderDirective) headers: QueryList<
    NgbdSortableHeaderDirective
  >;
  concept: Concept;
  documents: Document[] = [];
  page = 1;
  pageSize = 5;
  totalDocuments = 0;

  sortBy = 'date';
  sortDirection = 'desc';
  websiteSortIcon: IconDefinition = faSort;
  titleSortIcon: IconDefinition = faSort;
  dateSortIcon: IconDefinition = faSortDown;

  constructor(private route: ActivatedRoute, private apiService: ApiService) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiService.getConcept(params.get('conceptId'))
        )
      )
      .subscribe((concept) => {
        this.concept = concept;
        this.loadDocuments(this.paginateDocuments(this.page, this.pageSize));
      });
  }

  paginateDocuments(page: number, pageSize: number) {
    return this.concept.documentIds.slice(
      (page - 1) * pageSize,
      page * pageSize
    );
  }

  loadDocuments(documentIds: string[]) {
    this.documents = [];
    this.apiService
      .searchSolrDocuments(
        this.page,
        this.pageSize,
        this.concept.name,
        documentIds,
        this.sortBy,
        this.sortDirection
      )
      .subscribe((data) => {
        this.totalDocuments = data[0];
        const solrDocuments = data[1];
        this.documents = [];
        const solrDocumentIds = solrDocuments.map(solrDoc => solrDoc.id);
        this.getDocuments(solrDocumentIds).subscribe(documents => {
          documents.forEach((document, index) => {
            document.content = solrDocuments[index].content;
            this.documents.push(document);
          })
        })
      });
  }

  getDocuments(ids: string[]): Observable<any[]> {
    let docObservables = [];
    ids.forEach(id => {
      docObservables.push(this.apiService.getDocument(id));
    });
    return forkJoin(docObservables);
  }

  loadPage(page: number) {
    this.loadDocuments(this.paginateDocuments(page, this.pageSize));
  }

  onSort({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting documents, default date descending
    if (direction === '') {
      this.sortBy = 'date';
      this.sortDirection = 'desc';
      this.websiteSortIcon = faSort;
      this.titleSortIcon = faSort;
      this.dateSortIcon = faSortDown;
      this.loadDocuments(this.paginateDocuments(this.page, this.pageSize));
    } else {
      this.sortDirection = direction;
      this.sortBy = column;
      const sortIcon = direction === 'asc' ? faSortUp : faSortDown;
      if (column === 'title') {
        this.titleSortIcon = sortIcon;
        this.dateSortIcon = faSort;
        this.websiteSortIcon = faSort;
      } else if (column === 'date') {
        this.dateSortIcon = sortIcon;
        this.titleSortIcon = faSort;
        this.websiteSortIcon = faSort;
      } else {
        this.websiteSortIcon = sortIcon;
        this.titleSortIcon = faSort;
        this.dateSortIcon = faSort;
      }
      this.loadDocuments(this.paginateDocuments(this.page, this.pageSize));
    }
  }
}
