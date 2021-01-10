import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import { ReportingObligation } from 'src/app/shared/models/ro';
import { DirectivesModule } from '../../directives/directives.module';
import { AnnotatorDirective } from '../../directives/annotator.directive';

@Component({
  selector: 'app-ro-document-details',
  templateUrl: './ro-document-details.component.html',
  styleUrls: ['./ro-document-details.component.css'],
})
export class RoDocumentDetailsComponent implements OnInit {
  document: Document;
  ro: ReportingObligation;
  instanceType: string = "ro";
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
          this.service.getRo(params.get('roId'))
        )
      )
      .subscribe((ro) => {
        this.ro = ro;
        this.route.paramMap
          .pipe(
            switchMap((params: ParamMap) =>
              this.service.getDocument(params.get('documentId'))
            )
          )
          .subscribe((document) => {
            this.document = document;
            console.log(this.ro);
            this.service.searchSolrPreAnalyzedDocument(
              this.document.id,
              1,
              1,
              'maximum',
              'concept_occurs',
              [],
              'id',
              'asc'
            )
            .subscribe((data) => {
              console.log(data[1]["highlighting"]);
              console.log(this.document.id);
              this.content_html = "Lorem ipsum lorem ipsum."
              // this.content_html = data[1]["highlighting"][this.document.id][this.instanceType];
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
}
