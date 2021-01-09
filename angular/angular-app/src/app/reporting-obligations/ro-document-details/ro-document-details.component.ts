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
            this.route.paramMap.subscribe((params: ParamMap) => {
              this.term = "test";
              // this.term = this.ro.name;
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
                    // this.content_html = data[1]["highlighting"][this.document.id][this.instanceType];
                    this.content_html = "Dummy document text. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.";
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
}
