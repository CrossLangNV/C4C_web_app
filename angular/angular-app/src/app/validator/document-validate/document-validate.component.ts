import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import { SelectItem } from 'primeng/api/selectitem';
import { AcceptanceState } from 'src/app/shared/models/acceptanceState';
import { Comment } from 'src/app/shared/models/comment';
import { ApiAdminService } from 'src/app/core/services/api.admin.service';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import { AuthenticationService } from 'src/app/core/auth/authentication.service';
import { DjangoUser } from 'src/app/shared/models/django_user';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Attachment } from 'src/app/shared/models/attachment';
import { MessageService, ConfirmationService } from 'primeng/api';

@Component({
  selector: 'app-document-validate',
  templateUrl: './document-validate.component.html',
  styleUrls: ['./document-validate.component.css'],
  providers: [MessageService],
})
export class DocumentValidateComponent implements OnInit {
  document: Document;
  consolidatedVersions = new Map();
  stateValues: SelectItem[] = [];
  cities: SelectItem[];
  selectedCities: string[] = [];
  acceptanceState: AcceptanceState;
  comments: Comment[] = [];
  newComment: Comment;
  deleteIcon: IconDefinition;
  currentDjangoUser: DjangoUser;
  attachment: Attachment;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService,
    private adminService: ApiAdminService,
    private authenticationService: AuthenticationService,
    private modalService: NgbModal,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );
    this.attachment = new Attachment('', '', '', '', '');
    this.cities = [];
    this.cities.push({ label: 'Level 1', value: 'level1' });
    this.cities.push({ label: 'Level 2', value: 'level2' });
    this.cities.push({ label: 'Level 3', value: 'level3' });

    this.acceptanceState = new AcceptanceState('', '', '', '');
    this.newComment = new Comment('', '', '', '', new Date());
    this.service.getStateValues().subscribe((states) => {
      states.forEach((state) => {
        this.stateValues.push({ label: state, value: state });
      });
    });
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getDocument(params.get('documentId'))
        )
      )
      .subscribe((document) => {
        this.document = document;
        this.service
          .getSolrDocument(this.document.id)
          .subscribe((solrDocument) => {
            solrDocument[0].consolidated_versions.forEach((consolidated) => {
              let consolidatedDate = consolidated.split('-')[1];
              consolidatedDate = new Date(
                consolidatedDate.substring(0, 4) +
                  '-' +
                  consolidatedDate.substring(4, 6) +
                  '-' +
                  consolidatedDate.substring(6)
              );
              this.consolidatedVersions.set(consolidated, consolidatedDate);
            });
          });
        this.newComment.documentId = document.id;
        this.comments = [];
        if (document.commentIds) {
          document.commentIds.forEach((commentId) => {
            this.service.getComment(commentId).subscribe((comment) => {
              this.adminService.getUser(comment.userId).subscribe((user) => {
                comment.username = user.username;
              });
              this.comments.push(comment);
            });
          });
        }
      });
    this.deleteIcon = faTrashAlt;
  }

  onStateChange(event) {
    // FIXME: can we abract the the acceptanceState.id  via the API (should not be know externally ?)
    this.acceptanceState.id = this.document.acceptanceState;
    this.acceptanceState.value = event.value;
    this.acceptanceState.documentId = this.document.id;
    this.service.updateState(this.acceptanceState).subscribe((result) => {
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
    this.service.addComment(this.newComment).subscribe((comment) => {
      comment.username = this.currentDjangoUser.username;
      this.comments.push(comment);
      this.newComment.value = '';
      this.service.messageSource.next('refresh');
    });
  }

  onDeleteComment(comment: Comment) {
    this.confirmationService.confirm({
      message: 'Do you want to delete this comment?',
      accept: () => {
        this.service.deleteComment(comment.id).subscribe((response) => {
          this.comments = this.comments.filter(
            (item) => item.id !== comment.id
          );
          this.service.messageSource.next('refresh');
        });
      },
    });
  }

  openModal(targetModal, attachmentId: string) {
    this.attachment = new Attachment('', '', '', '', '');
    this.modalService.open(targetModal, {
      centered: true,
      backdrop: 'static',
      size: 'xl',
      scrollable: true,
    });

    if (attachmentId.startsWith('CELEX:')) {
      attachmentId = attachmentId.replace(/CELEX:/g, '');
      this.service.getEURLEXxhtml(attachmentId).subscribe((xhtml) => {
        this.attachment = new Attachment(
          attachmentId,
          '',
          this.document.url,
          '',
          xhtml
        );
        console.log(this.attachment.url);
      });
    } else {
      this.service.getAttachment(attachmentId).subscribe((attachment) => {
        attachment.content = '<pre>' + attachment.content + '</pre>';
        this.attachment = attachment;
      });
    }
  }

  onSubmit() {
    this.modalService.dismissAll();
  }

  goToLink(url: string) {
    window.open(url, '_blank');
  }
}
