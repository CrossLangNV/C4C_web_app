import { Component, OnInit, Directive, Input, Output, EventEmitter, ViewChildren, QueryList } from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { Concept } from 'src/app/shared/models/concept';
import { Document } from 'src/app/shared/models/document';

import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {faSort, faSortUp, faSortDown, faTrashAlt} from '@fortawesome/free-solid-svg-icons';
import { Observable, forkJoin } from 'rxjs';
import { SelectItem } from 'primeng/api/selectitem';
import {ConceptAcceptanceState} from "../../shared/models/conceptAcceptanceState";
import {ConceptComment} from "../../shared/models/conceptComment";
import {ApiAdminService} from "../../core/services/api.admin.service";
import { MessageService, ConfirmationService } from 'primeng/api';
import {DjangoUser} from "../../shared/models/django_user";
import {AuthenticationService} from "../../core/auth/authentication.service";

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
export class ConceptDetailSortableHeaderDirective {
  @Input() sortable: string;
  @Input() direction: SortDirection = '';
  @Output() sortDetail = new EventEmitter<SortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.sortDetail.emit({ column: this.sortable, direction: this.direction });
  }
}

@Component({
  selector: 'app-concept-detail',
  templateUrl: './concept-detail.component.html',
  styleUrls: ['./concept-detail.component.css'],
  providers: [MessageService],
})
export class ConceptDetailComponent implements OnInit {
  @ViewChildren(ConceptDetailSortableHeaderDirective) headers: QueryList<
    ConceptDetailSortableHeaderDirective
  >;
  concept: Concept;

  // AcceptanceState and comments
  stateValues: SelectItem[] = [];
  acceptanceState: ConceptAcceptanceState;
  comments: ConceptComment[] = [];
  newComment: ConceptComment;
  deleteIcon: IconDefinition;
  currentDjangoUser: DjangoUser;

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

  constructor(
    private route: ActivatedRoute,
    private service: ApiService,
    private adminService: ApiAdminService,
    private messageService: MessageService,
    private authenticationService: AuthenticationService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );
    this.acceptanceState = new ConceptAcceptanceState('', '', '', '')
    this.newComment = new ConceptComment('', '', '', '', new Date());

    this.service.getConceptStateValues().subscribe((states) => {
      states.forEach((state) => {
        this.stateValues.push({ label: state, value: state });
      });
    });

    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getConcept(params.get('conceptId'))
        )
      )
      .subscribe((concept) => {
        this.concept = concept;

        this.newComment.conceptId = concept.id;
        this.comments = [];

        if (concept.commentIds) {
          concept.commentIds.forEach((commentId) => {
            this.service.getConceptComment(commentId).subscribe((comment) => {
              this.adminService.getUser(comment.userId).subscribe((user) => {
                comment.username = user.username;
              });
              this.comments.push(comment);
            });
          });
        }

        this.loadOccursInDocuments();
        this.loadDefinedInDocuments();
      });
    this.deleteIcon = faTrashAlt;
  }

  onStateChange(event) {
    // FIXME: can we abract the the acceptanceState.id  via the API (should not be know externally ?)
    this.acceptanceState.id = this.concept.acceptanceState;
    this.acceptanceState.value = event.value;
    this.acceptanceState.conceptId = this.concept.id;
    this.service.updateConceptState(this.acceptanceState).subscribe((result) => {
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

  onAddComment() {
    this.service.addConceptComment(this.newComment).subscribe((comment) => {
      comment.username = this.currentDjangoUser.username;
      this.comments.push(comment);
      this.newComment.value = '';
      this.service.messageSource.next('refresh');
    });
  }

  onDeleteComment(comment: ConceptComment) {
    this.confirmationService.confirm({
      message: 'Do you want to delete this comment?',
      accept: () => {
        this.service.deleteConceptComment(comment.id).subscribe((response) => {
          this.comments = this.comments.filter(
            (item) => item.id !== comment.id
          );
          this.service.messageSource.next('refresh');
        });
      },
    });
  }

  loadOccursInDocumentsPreAnalyzed() {
    this.service
      .searchSolrPreAnalyzedDocuments(
        this.occursInPage,
        this.occursInPageSize,
        this.concept.name,
        "concept_occurs",
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
            document.content = solrDocuments[index].concept_occurs;
            this.occursIn.push(document);
          });
        });
      });
  }

  loadOccursInDocuments() {
    this.service
      .searchSolrDocuments(
        this.occursInPage,
        this.occursInPageSize,
        this.concept.name,
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

  // highlightedContent contains html where concepts are enclosed by <span class="highlight">concept</span>
  getOffsets(highlightedContent: string, concept: string) {

  }

  loadDefinedInDocuments() {
    this.service
      .searchSolrPreAnalyzedDocuments(
        this.definedInPage,
        this.definedInPageSize,
        this.concept.definition,
        "concept_defined",
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
            let solrContent = solrDocuments[index].concept_defined;
            // solrContent = solrContent.map(text => text.replace('<span class=\"highlight\">means</span>', 'means'));
            document.content = solrContent;
            this.definedIn.push(document);
          });
        });
      });
  }

  getDocuments(ids: string[]): Observable<any[]> {
    let docObservables = [];
    ids.forEach((id) => {
      docObservables.push(this.service.getDocument(id));
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
