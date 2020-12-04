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
import {SelectItem} from "primeng/api/selectitem";
import {ConceptAcceptanceState} from "../../shared/models/conceptAcceptanceState";
import {ConceptComment} from "../../shared/models/conceptComment";
import {DjangoUser} from "../../shared/models/django_user";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {RoAcceptanceState} from "../../shared/models/roAcceptanceState";
import {MessageService} from "primeng/api";

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
  providers: [MessageService]
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
  collectionSize = 0;

  definedIn: Document[] = [];
  definedInPage = 1;
  definedInPageSize = 5;
  definedInTotal = 0;
  definedInSortBy = 'date';
  definedInSortDirection = 'desc';
  definedInDateSortIcon: IconDefinition = faSortDown;

  // AcceptanceState and comments
  stateValues: SelectItem[] = [];
  acceptanceState: RoAcceptanceState;
  comments: ConceptComment[] = [];
  newComment: ConceptComment; // TODO CHANGE
  deleteIcon: IconDefinition;
  currentDjangoUser: DjangoUser;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private authenticationService: AuthenticationService,
    private service: ApiService,
    private messageService: MessageService,
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );
    this.acceptanceState = new RoAcceptanceState('', '', '', '')
    this.newComment = new ConceptComment('', '', '', '', new Date()); // TODO Change

    this.service.getRoStateValues().subscribe((states) => {
      states.forEach((state) => {
        this.stateValues.push({ label: state, value: state });
      });
    });

    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiService.getRo(params.get('roId'))
        )
      )
      .subscribe((concept) => {
        this.ro = concept;
        this.loadOccursInDocuments();
      });
  }

  loadOccursInDocuments() {
    this.apiService
      .searchSolrDocuments(
        this.occursInPage,
        this.occursInPageSize,
        this.ro.definition,
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
            this.collectionSize = solrDocumentIds.count;
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

  onStateChange(event) {
    // FIXME: can we abract the the acceptanceState.id  via the API (should not be know externally ?)
    this.acceptanceState.id = this.ro.acceptanceState;
    this.acceptanceState.value = event.value;
    this.acceptanceState.roId = this.ro.id;
    this.service.updateRoState(this.acceptanceState).subscribe((result) => {
      // Update document list
      this.service.messageSource.next('refresh');
      let severity = {
        Accepted: 'success',
        Rejected: 'error',
        Unvalidated: 'info',
      };
      this.messageService.add({
        severity: severity[event.value],
        summary: 'Acceptance State',
        detail: 'Set to "' + event.value + '"',
      });
    });
  }


}
