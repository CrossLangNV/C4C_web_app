import { Component, OnInit, Directive, Input, Output, EventEmitter, ViewChildren, QueryList } from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { Concept } from 'src/app/shared/models/concept';
import { Document } from 'src/app/shared/models/document';

import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faSort, faSortUp, faSortDown } from '@fortawesome/free-solid-svg-icons';
import { Observable, forkJoin } from 'rxjs';
import { ReportingObligation } from 'src/app/shared/models/ro';

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
export class RoDetailSortableHeaderDirective {
  @Input() sortable: string;
  @Input() direction: SortDirection = '';
  @Output() sortDetail = new EventEmitter<SortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.sortDetail.emit({ column: this.sortable, direction: this.direction });
  }
}

@Component({
  selector: 'app-ro-detail',
  templateUrl: './ro-detail.component.html',
  styleUrls: ['./ro-detail.component.css'],
})
export class RoDetailComponent implements OnInit {
  @ViewChildren(RoDetailSortableHeaderDirective) headers: QueryList<
    RoDetailSortableHeaderDirective
  >;
  ro: ReportingObligation;

  occursIn: Document[] = [];
  occursInPage = 1;
  occursInPageSize = 5;
  occursInTotal = 0;
  occursInSortBy = 'date';
  occursInSortDirection = 'desc';
  occursInDateSortIcon: IconDefinition = faSortDown;

  definedIn: Document[] = [];
  definedInPage = 1;
  definedInPageSize = 5;
  definedInTotal = 0;
  definedInSortBy = 'date';
  definedInSortDirection = 'desc';
  definedInDateSortIcon: IconDefinition = faSortDown;

  constructor(private route: ActivatedRoute, private apiService: ApiService) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiService.getRo(params.get('roId'))
        )
      )
      .subscribe((concept) => {
        this.ro = concept;
        this.loadOccursInDocuments();
        this.loadDefinedInDocuments();
      });
  }

  loadOccursInDocuments() {
    this.apiService
      .searchSolrDocuments(
        this.occursInPage,
        this.occursInPageSize,
        this.ro.name,
        [],
        this.occursInSortBy,
        this.occursInSortDirection
      )
      .subscribe((data) => {
        this.occursInTotal = data[0];
        const solrDocuments = data[1];
        this.occursIn = [];
        const solrDocumentIds = solrDocuments.map((solrDoc) => solrDoc.id);
        this.getDocuments(solrDocumentIds).subscribe((doc) => {
          doc.forEach((document, index) => {
            document.content = solrDocuments[index].content;
            this.occursIn.push(document);
          });
        });
      });
  }

  loadDefinedInDocuments() {
    this.apiService
      .searchSolrDocuments(
        this.definedInPage,
        this.definedInPageSize,
        this.ro.name + ' means',
        [],
        this.definedInSortBy,
        this.definedInSortDirection
      )
      .subscribe((data) => {
        this.definedInTotal = data[0];
        const solrDocuments = data[1];
        this.definedIn = [];
        const solrDocumentIds = solrDocuments.map((solrDoc) => solrDoc.id);
        this.getDocuments(solrDocumentIds).subscribe((doc) => {
          doc.forEach((document, index) => {
            let solrContent = solrDocuments[index].content;
            solrContent = solrContent.map(text => text.replace('<span class=\"highlight\">means</span>', 'means'));
            document.content = solrContent;
            this.definedIn.push(document);
          });
        });
      });
  }

  getDocuments(ids: string[]): Observable<any[]> {
    let docObservables = [];
    ids.forEach((id) => {
      docObservables.push(this.apiService.getDocument(id));
    });
    return forkJoin(docObservables);
  }

  loadOccursInPage(page: number) {
    this.occursInPage = page;
    this.loadOccursInDocuments();
  }

  loadDefinedInPage(page: number) {
    this.definedInPage = page;
    this.loadDefinedInDocuments();
  }

  onSortOccursIn({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting occursIn, default date descending
    if (direction === '') {
      this.occursInSortBy = 'date';
      this.occursInSortDirection = 'desc';
      this.occursInDateSortIcon = faSortDown;
      this.loadOccursInDocuments();
    } else {
      this.occursInSortDirection = direction;
      this.occursInSortBy = column;
      const sortIcon = direction === 'asc' ? faSortUp : faSortDown;
      if (column === 'date') {
        this.occursInDateSortIcon = sortIcon;
      } else {
        this.occursInDateSortIcon = faSort;
      }
      this.loadOccursInDocuments();
    }
  }

  onSortDefinedIn({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting definedIn, default date descending
    if (direction === '') {
      this.definedInSortBy = 'date';
      this.definedInSortDirection = 'desc';
      this.definedInDateSortIcon = faSortDown;
      this.loadDefinedInDocuments();
    } else {
      this.definedInSortDirection = direction;
      this.definedInSortBy = column;
      const sortIcon = direction === 'asc' ? faSortUp : faSortDown;
      if (column === 'date') {
        this.definedInDateSortIcon = sortIcon;
      } else {
        this.definedInDateSortIcon = faSort;
      }
      this.loadDefinedInDocuments();
    }
  }
}
