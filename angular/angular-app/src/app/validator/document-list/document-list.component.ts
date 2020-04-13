import { Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { Document } from 'src/app/shared/models/document';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css'],
})
export class DocumentListComponent implements OnInit {
  documents$: Observable<Document[]>;
  selectedId: number;
  pageId: number;
  collectionSize: number;
  autoValidatedSize: number;
  autoRejectedSize: number;

  searchTerm = '';
  searchTermChanged: Subject<string> = new Subject<string>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {}

  ngOnInit() {
    this.collectionSize = 9348; // FIXME read from results
    this.autoRejectedSize = 1043;
    this.autoValidatedSize = this.collectionSize - this.autoRejectedSize;
    this.documents$ = this.route.paramMap.pipe(
      switchMap((params) => {
        // (+) before `params.get()` turns the string into a number
        this.selectedId = +params.get('id');
        this.pageId = +params.get('pageId');
        return this.service.getDocuments(5);
      })
    );
  }
}
