import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Website } from '../../shared/models/website';
import { Document, DocumentResults } from '../../shared/models/document';
import { Router } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faTrashAlt, faPlus } from '@fortawesome/free-solid-svg-icons';
import { ConfirmationService } from 'primeng/api';
import { ApiAdminService } from 'src/app/core/services/api.admin.service';
import { AcceptanceState } from 'src/app/shared/models/acceptanceState';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-website-details',
  templateUrl: './website-details.component.html',
  styleUrls: ['./website-details.component.css'],
})
export class WebsiteDetailsComponent implements OnInit {
  website: Website;
  documents: Document[] = [];
  titleIsBeingEdited = false;
  urlIsBeingEdited = false;
  contentIsBeingEdited = false;
  deleteIcon: IconDefinition;
  addIcon: IconDefinition;
  adminMode = false;
  acceptanceStates: AcceptanceState[] = [];
  acceptanceStatesByDocument = new Map<string, AcceptanceState[]>();
  page = 1;
  pageSize = 5;
  totalDocuments = 0;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private apiAdminService: ApiAdminService,
    private router: Router,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.apiService.isAdmin().subscribe((isAdmin) => {
      this.adminMode = isAdmin;
      if (isAdmin) {
        this.apiAdminService.getStates().subscribe((states) => {
          this.acceptanceStates = states;
        });
      }
      this.route.paramMap
        .pipe(
          switchMap((params: ParamMap) =>
            this.apiService.getWebsite(params.get('websiteId'))
          )
        )
        .subscribe((website) => {
          this.website = website;
          this.totalDocuments = website.totalDocuments;
          this.loadDocuments(
            this.paginateDocuments(this.page, this.pageSize),
            isAdmin
          );
        });
    });
    this.deleteIcon = faTrashAlt;
    this.addIcon = faPlus;
  }

  paginateDocuments(page: number, pageSize: number) {
    return this.apiService.getDocumentResults(page, '', '', '', this.website.name, false, '', '-date')
  }

  loadDocuments(documentResults: Observable<DocumentResults>, isAdmin: boolean) {
    this.documents = [];
    documentResults.subscribe(result =>
      result.results.forEach((document) => {
        if (isAdmin) {
          const docAcceptanceStates = this.acceptanceStates.filter(
            (state) => state.documentId === document.id
          );
          docAcceptanceStates.map((state) => {
            this.apiAdminService.getUser(state.userId).subscribe((user) => {
              state.username = user.username;
            });
          });
          this.acceptanceStatesByDocument.set(document.id, docAcceptanceStates);
          this.documents.push(document);
        } else {
          this.apiService
            .getState(document.acceptanceState)
            .subscribe((state) => {
              document.acceptanceState = state.value;
              this.documents.push(document);
            });
        }
      })
    );
  }

  loadPage(page: number) {
    this.loadDocuments(
      this.paginateDocuments(page, this.pageSize),
      this.adminMode
    );
  }

  onDelete() {
    this.confirmationService.confirm({
      message: 'Do you want to delete this website?',
      accept: () => {
        this.apiService
          .deleteWebsite(this.website.id)
          .subscribe((website) => this.router.navigate(['/websites']));
      },
    });
  }

  onNameChanged(event: any) {
    this.website.name = event.target.value;
    this.apiService.updateWebsite(this.website).subscribe((website) => {
      this.website = website as Website;
      this.titleIsBeingEdited = false;
    });
  }

  onUrlChanged(event: any) {
    this.website.url = event.target.value;
    this.apiService.updateWebsite(this.website).subscribe((website) => {
      this.website = website as Website;
      this.urlIsBeingEdited = false;
    });
  }

  onContentChanged(event: any) {
    event.preventDefault();
    this.website.content = event.target.value;
    this.apiService.updateWebsite(this.website).subscribe((website) => {
      this.website = website as Website;
      this.contentIsBeingEdited = false;
    });
  }
}
