import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import { Concept } from 'src/app/shared/models/concept';
import { DirectivesModule } from '../../directives/directives.module';
import { AnnotatorDirective } from '../../directives/annotator.directive';

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
  term: string = "unknown";
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
              if (this.annotationType == "occurence") {
                this.instanceType = "concept_occurs";
                this.term = this.concept.name;
              }
              if (this.annotationType == "definition") {
                this.instanceType = "concept_defined";
                this.term = this.concept.definition;
              }
              this.service
              .getDocumentWithContent(document.id)
              .subscribe((doc) => {
                this.service
                  .searchSolrPreAnalyzedDocument(
                    this.document.id,
                    1,
                    1,
                    this.term,
                    this.instanceType,
                    [],
                    "id",
                    "asc"
                  )
                  .subscribe((data) => {
                    this.content_html = data[1]["highlighting"][this.document.id][this.instanceType];
                  });
              });
            });
          });
      });
  }

  highlight(xhtml, concept): String {
    var searchMask = concept.name;
    var regEx = new RegExp(searchMask, 'ig');
    var replaceMask = '<span class="highlight">' + concept.name + '</span>';
    return xhtml.replace(regEx, replaceMask);
  }
  
  goToLink(url: string) {
    window.open(url, '_blank');
  }
}
