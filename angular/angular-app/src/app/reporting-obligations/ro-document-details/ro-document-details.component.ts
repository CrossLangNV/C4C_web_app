import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';

@Component({
  selector: 'app-ro-document-details',
  templateUrl: './ro-document-details.component.html',
  styleUrls: ['./ro-document-details.component.css'],
})
export class RoDocumentDetailsComponent implements OnInit {
  document: Document;
  consolidatedVersions = new Map();
  content_html: String;
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {}

  ngOnInit(): void {
    // this.route.paramMap
    //   .pipe(
    //     switchMap((params: ParamMap) =>
    //       this.service.getConcept(params.get('conceptId'))
    //     )
    //   )
    //   .subscribe((concept) => {
    //     this.concept = concept;
    //     this.route.paramMap
    //       .pipe(
    //         switchMap((params: ParamMap) =>
    //           this.service.getDocument(params.get('documentId'))
    //         )
    //       )
    //       .subscribe((document) => {
    //         this.document = document;
    //         this.service.getEURLEXxhtml(document.celex).subscribe((xhtml) => {
    //           this.content_html = this.highlight(xhtml, concept);
    //           // this.service
    //           //   .getSolrDocument(this.document.id)
    //           //   .subscribe((solrDocument) => {
    //           //     this.consolidatedVersions = new Map();
    //           //   });
    //         });
    //       });
    //   });
  }

  highlight(xhtml, concept): String {
    var searchMask = concept.name;
    var regEx = new RegExp(searchMask, 'ig');
    var replaceMask = '<span class="highlight">' + concept.name + '</span>';
    return xhtml.replace(regEx, replaceMask);
  }
}
