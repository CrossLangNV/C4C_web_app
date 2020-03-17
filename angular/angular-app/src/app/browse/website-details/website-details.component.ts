import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Website } from '../../shared/models/website';
import { Document } from '../../shared/models/document';
import { Router } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faTrashAlt, faPlus } from '@fortawesome/free-solid-svg-icons';
import { SelectItem, ConfirmationService } from 'primeng/api';

@Component({
  selector: 'app-website-details',
  templateUrl: './website-details.component.html',
  styleUrls: ['./website-details.component.css']
})
export class WebsiteDetailsComponent implements OnInit {
  website: Website;
  documents: Document[] = [];
  titleIsBeingEdited: boolean = false;
  urlIsBeingEdited: boolean = false;
  contentIsBeingEdited: boolean = false;
  deleteIcon: IconDefinition;
  addIcon: IconDefinition;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiService.getWebsite(params.get('websiteId'))
        )
      )
      .subscribe(website => {
        this.website = website;
        website.documentIds.forEach(id => {
          this.apiService.getDocument(id).subscribe(document => {
            this.documents.push(document);
          });
        });
      });
    this.deleteIcon = faTrashAlt;
    this.addIcon = faPlus;
  }

  onDelete() {
    this.confirmationService.confirm({
      message: 'Do you want to delete this website?',
      accept: () => {
        this.apiService.deleteWebsite(this.website.id).subscribe();
        this.router.navigate(['/website/']);
      }
    });

    this.apiService.deleteWebsite(this.website.id).subscribe(
      res => this.router.navigate(['/website']),
      err => console.log(err)
    );
  }

  onNameChanged(event: any) {
    this.website.name = event.target.value;
    this.apiService.updateWebsite(this.website).subscribe(website => {
      this.website = website as Website;
      this.titleIsBeingEdited = false;
    });
  }

  onUrlChanged(event: any) {
    this.website.url = event.target.value;
    this.apiService.updateWebsite(this.website).subscribe(website => {
      this.website = website as Website;
      this.urlIsBeingEdited = false;
    });
  }

  onContentChanged(event: any) {
    this.website.content = event.target.value;
    this.apiService.updateWebsite(this.website).subscribe(website => {
      this.website = website as Website;
      this.contentIsBeingEdited = false;
    });
  }
}
