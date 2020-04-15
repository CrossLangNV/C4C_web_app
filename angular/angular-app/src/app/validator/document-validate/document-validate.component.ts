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
import { AuthenticationService } from 'src/app/core/auth/authentication.service';
import { DjangoUser } from 'src/app/shared/models/django_user';
import { compileNgModuleFromRender2 } from '@angular/compiler/src/render3/r3_module_compiler';

@Component({
  selector: 'app-document-validate',
  templateUrl: './document-validate.component.html',
  styleUrls: ['./document-validate.component.css'],
})
export class DocumentValidateComponent implements OnInit {
  document$: Observable<Document>;
  stateValues: SelectItem[] = [];
  cities: SelectItem[];
  selectedCities: string[] = [];
  acceptanceState: AcceptanceState;
  comments: Comment[] = [];
  newComment: Comment;
  deleteIcon: IconDefinition;
  currentDjangoUser: DjangoUser;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService,
    private adminService: ApiAdminService,
    private authenticationService: AuthenticationService
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );
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
    this.document$ = this.route.paramMap.pipe(
      switchMap((params: ParamMap) =>
        this.service.getDocument(params.get('documentId'))
      )
    );
    this.document$.subscribe((document) => {
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
}
