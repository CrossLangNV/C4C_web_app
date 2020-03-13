import { Component, OnInit } from '@angular/core';
import { Document } from 'src/app/shared/models/document';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { faTrashAlt } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-document-details',
  templateUrl: './document-details.component.html',
  styleUrls: ['./document-details.component.css']
})
export class DocumentDetailsComponent implements OnInit {
  document: Document;
  deleteIcon: IconDefinition;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiService.getDocument(params.get('documentId'))
        )
      )
      .subscribe(document => {
        this.document = document;
      });
    this.deleteIcon = faTrashAlt;
  }
}
