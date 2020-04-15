import { Observable } from 'rxjs';
import { switchMap, distinctUntilChanged, debounceTime } from 'rxjs/operators';
import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { Document, DocumentResults } from 'src/app/shared/models/document';
import { Subject } from 'rxjs';
import { Tag } from 'src/app/shared/models/tag';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css'],
})
export class DocumentListComponent implements OnInit {
  documents$: Document[];
  documentsResults$: Observable<DocumentResults>;
  selectedId: number;
  page = 2;
  pageSize = 5;
  collectionSize = 0;
  autoValidatedSize = 0;
  autoRejectedSize = 0;
  filterType: string;
  keyword: string;

  searchTermChanged: Subject<string> = new Subject<string>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {}

  ngOnInit() {
    this.service
      .getDocumentResults(this.page, this.keyword)
      .subscribe((result) => {
        this.documents$ = result.results;
        this.collectionSize = result.count;
        this.autoRejectedSize = 0;
        this.autoValidatedSize = 0;
      });
    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.service
          .getDocumentResults(this.page, this.keyword)
          .subscribe((result) => {
            this.documents$ = result.results;
            this.collectionSize = result.count;
            this.autoRejectedSize = 0;
            this.autoValidatedSize = 0;
          });
      });
  }

  onSearch(keyword: string) {
    console.log('TERM:' + keyword);
    this.searchTermChanged.next(keyword);
  }

  onAddTag(event, documentId) {
    const newTag = new Tag('', event.value, documentId);
    this.service.addTag(newTag).subscribe();
  }

  onRemoveTag(event) {

  }

  loadPage(pg: number) {
    console.log('PAGE:' + this.page);
    this.service
      .getDocumentResults(this.page, this.keyword)
      .subscribe((result) => {
        this.documents$ = result.results;
        this.collectionSize = result.count;
        this.autoRejectedSize = 0;
        this.autoValidatedSize = 0;
      });
  }
}
