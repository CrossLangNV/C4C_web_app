import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { Observable } from 'rxjs';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import { SelectItem } from 'primeng/api/selectitem';
import { AcceptanceState } from 'src/app/shared/models/acceptanceState';
import { Comment } from 'src/app/shared/models/comment';
import { ApiAdminService } from 'src/app/core/services/api.admin.service';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faTrashAlt } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-document-validate',
  templateUrl: './document-validate.component.html',
  styleUrls: ['./document-validate.component.css'],
})
export class DocumentValidateComponent implements OnInit {
  document$: Observable<Document>;
  stateValues: SelectItem[] = [];
  acceptanceState: AcceptanceState;
  comments: Comment[] = [];
  newComment: Comment;
  deleteIcon: IconDefinition;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService,
    private adminService: ApiAdminService
  ) {}

  ngOnInit() {
    this.acceptanceState = new AcceptanceState('', '', '', '');
    this.newComment = new Comment('', '', '', '');
    this.service.getStateValues().subscribe((states) => {
      states.forEach((state) => {
        this.stateValues.push({ label: state, value: state });
      });
    });
    this.document$ = this.route.paramMap.pipe(
      switchMap((params: ParamMap) =>
        this.service.getDocument(params.get('documentId'))
      )
    );
    this.document$.subscribe((document) => {
      this.newComment.documentId = document.id;
      if (document.commentIds) {
        this.comments = [];
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
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getDocument(params.get('documentId'))
        )
      )
      .subscribe((document) => {
        // FIXME: can we abract the the acceptanceState.id  via the API (should not be know externally ?)
        this.acceptanceState.id = document.acceptanceState;
        this.acceptanceState.value = event.value;
        this.acceptanceState.documentId = document.id;
        this.service.updateState(this.acceptanceState).subscribe();
      });
  }

  onAddComment() {
    this.service.addComment(this.newComment).subscribe((comment) => {
      this.router
        .navigateByUrl('/validator', { skipLocationChange: true })
        .then(() => this.router.navigate(['/validator']));
    });
  }

  onDeleteComment(comment: Comment) {
    this.service.deleteComment(comment.id).subscribe((comment) => {
      this.router
        .navigateByUrl('/validator', { skipLocationChange: true })
        .then(() => this.router.navigate(['/validator']));
    });
  }
}
