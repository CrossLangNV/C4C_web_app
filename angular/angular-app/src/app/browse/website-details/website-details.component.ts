import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { ApiServiceWebsites } from '../../core/services/api.service.websites';
import { Website } from '../../shared/models/website';
import { Router } from '@angular/router';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-website-details',
  templateUrl: './website-details.component.html',
  styleUrls: ['./website-details.component.css']
})
export class WebsiteDetailsComponent implements OnInit {
  website;
  titleIsBeingEdited: boolean = false;
  urlIsBeingEdited: boolean = false;
  contentIsBeingEdited: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private apiServiceWebsites: ApiServiceWebsites,
    private router: Router
  ) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiServiceWebsites.getWebsite(params.get('websiteId'))
        )
      )
      .subscribe(website => (this.website = website));
  }

  onDelete() {
    this.apiServiceWebsites.deleteWebsite(this.website.id).subscribe(
      res => this.router.navigate(['/website']),
      err => console.log(err)
    );
  }

  onNameChanged(event: any) {
    this.website.name = event.target.value;
    this.apiServiceWebsites.updateWebsite(this.website).subscribe(website => {
      this.website = website as Website;
      this.titleIsBeingEdited = false;
    });
  }

  onUrlChanged(event: any) {
    this.website.url = event.target.value;
    this.apiServiceWebsites.updateWebsite(this.website).subscribe(website => {
      this.website = website as Website;
      this.urlIsBeingEdited = false;
    });
  }

  onContentChanged(event: any) {
    this.website.content = event.target.value;
    this.apiServiceWebsites.updateWebsite(this.website).subscribe(website => {
      this.website = website as Website;
      this.contentIsBeingEdited = false;
    });
  }
}
