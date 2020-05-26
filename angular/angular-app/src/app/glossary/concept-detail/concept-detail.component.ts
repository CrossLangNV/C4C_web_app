import { Component, OnInit } from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { Concept } from 'src/app/shared/models/concept';
import { Document } from 'src/app/shared/models/document';

@Component({
  selector: 'app-concept-detail',
  templateUrl: './concept-detail.component.html',
  styleUrls: ['./concept-detail.component.css'],
})
export class ConceptDetailComponent implements OnInit {
  concept: Concept;
  documents: Document[] = [];
  page = 1;
  pageSize = 5;
  totalDocuments = 0;

  constructor(private route: ActivatedRoute, private apiService: ApiService) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.apiService.getConcept(params.get('conceptId'))
        )
      )
      .subscribe((concept) => {
        this.concept = concept;
        this.totalDocuments = concept.documentIds.length;
        this.loadDocuments(this.paginateDocuments(this.page, this.pageSize));
      });
  }

  paginateDocuments(page: number, pageSize: number) {
    return this.concept.documentIds.slice(
      (page - 1) * pageSize,
      page * pageSize
    );
  }

  loadDocuments(documentIds: string[]) {
    this.documents = [];
    documentIds.forEach((id) => {
      this.apiService.getDocument(id).subscribe((document) => {
        this.apiService
          .getState(document.acceptanceState)
          .subscribe((state) => {
            document.acceptanceState = state.value;
            this.documents.push(document);
          });
      });
    });
  }

  loadPage(page: number) {
    this.loadDocuments(this.paginateDocuments(page, this.pageSize));
  }
}
