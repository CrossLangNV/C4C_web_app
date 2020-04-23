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

@Component({
  selector: 'app-document-validate',
  templateUrl: './document-validate.component.html',
  styleUrls: ['./document-validate.component.css'],
})
export class DocumentValidateComponent implements OnInit {
  document: Document;
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
    private modalService: NgbModal
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
    this.route.paramMap.pipe(
      switchMap((params: ParamMap) =>
        this.service.getDocumentSyncWithAttachments(params.get('documentId'))
      )
    ).subscribe((document) => {
      this.document = document;
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
    this.service.updateState(this.acceptanceState).subscribe();
  }

  onAddComment() {
    this.service.addComment(this.newComment).subscribe((comment) => {
      comment.username = this.currentDjangoUser.username;
      this.comments.push(comment);
      this.newComment.value = '';
    });
  }

  onDeleteComment(comment: Comment) {
    this.service.deleteComment(comment.id).subscribe((response) => {
      this.comments = this.comments.filter((item) => item.id !== comment.id);
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
        this.attachment = new Attachment(attachmentId, '', '', '', xhtml);
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
}
