import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import { Concept } from 'src/app/shared/models/concept';

@Component({
  selector: 'app-concept-document-details',
  templateUrl: './concept-document-details.component.html',
  styleUrls: ['./concept-document-details.component.css'],
})
export class ConceptDocumentDetailsComponent implements OnInit {
  document: Document;
  concept: Concept;
  annotationType: String;
  instanceType: string = "unknown";
  consolidatedVersions = new Map();
  content_html: String;
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {}

  ngOnInit(): void {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getConcept(params.get('conceptId'))
        )
      )
      .subscribe((concept) => {
        this.concept = concept;
        this.route.paramMap
          .pipe(
            switchMap((params: ParamMap) => 
                this.service.getDocument(params.get('documentId'))
            )
          )
          .subscribe((document) => {
            this.document = document;

            this.route.paramMap.subscribe((params: ParamMap) => {
              this.annotationType = params.get('annotationType');
              if (this.annotationType == "occurence")
                this.instanceType = "concept_occurs";
              if (this.annotationType == "definition")
                this.instanceType = "concept_defined";
              this.service
              .getDocumentWithContent(document.id)
              .subscribe((doc) => {
                // this.content_html = doc.content;

                // this.service
                //   .getSolrDocument(this.document.id)
                //   .subscribe((solrDocument) => {
                //     this.consolidatedVersions = new Map();
                //   });

                this.service
                  .searchSolrPreAnalyzedDocument(
                    this.document.id,
                    1,
                    1,
                    this.concept.definition,
                    this.instanceType,
                    [],
                    "id",
                    "asc"
                  )
                  .subscribe((data) => {
                    this.content_html = data[1]["highlighting"][this.document.id][this.instanceType];
                  });
              
                // loadDefinedInDocuments() {
                //   this.service
                //     .searchSolrPreAnalyzedDocuments(
                //       this.definedInPage,
                //       this.definedInPageSize,
                //       this.concept.definition,
                //       "concept_defined",
                //       [],
                //       this.definedInSortBy,
                //       this.definedInSortDirection
                //     )
                //     .subscribe((data) => {
                //       this.definedInTotal = data[0];
                //       this.definedIn = data[1];
                //     });
                // }
              });
            });
          });
      });
  }
}
