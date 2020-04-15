import { Observable } from 'rxjs';
import { switchMap, distinctUntilChanged, debounceTime } from 'rxjs/operators';
import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { Document, DocumentResults } from 'src/app/shared/models/document';
import { Subject } from 'rxjs';
import { Tag } from 'src/app/shared/models/tag';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faUserAlt } from '@fortawesome/free-solid-svg-icons';

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
  filterType: string = 'none';
  keyword: string;
  userIcon: IconDefinition;
  filters = [
    { id: 'none', name: 'Filter..' },
    { id: 'own', name: '..Validated by me' },
    { id: 'unvalidated', name: '..Unvalidated' },
    { id: 'accepted', name: '..Accepted' },
    { id: 'rejected', name: '..Rejected' },
  ];
  searchTermChanged: Subject<string> = new Subject<string>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {}

  fetchDocuments() {
    this.service
      .getDocumentResults(this.page, this.keyword, this.filterType)
      .subscribe((result) => {
        this.documents$ = result.results;
        this.collectionSize = result.count;
        this.autoRejectedSize = 0;
        this.autoValidatedSize = 0;
      });
  }
  ngOnInit() {
    this.userIcon = faUserAlt;
    this.fetchDocuments();
    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.fetchDocuments();
      });
  }

  onSearch(keyword: string) {
    this.searchTermChanged.next(keyword);
  }

  onAddTag(event, tags, documentId) {
    const newTag = new Tag('', event.value, documentId);
    this.service.addTag(newTag).subscribe((addedTag) => {
      // primeng automatically adds the string value first, delete this as workaround
      // see: https://github.com/primefaces/primeng/issues/3419
      tags.splice(-1, 1);
      // now add the tag object
      tags.push(addedTag);
    });
  }

  onRemoveTag(event) {
    this.service.deleteTag(event.value.id).subscribe();
  }

  loadPage(pg: number) {
    this.fetchDocuments();
  }
}
