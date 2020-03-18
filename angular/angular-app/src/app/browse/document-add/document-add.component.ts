import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';

import { Document } from '../../shared/models/document';
import { SelectItem } from 'primeng/api/selectitem';

@Component({
  selector: 'app-document-add',
  templateUrl: './document-add.component.html',
  styleUrls: ['./document-add.component.css']
})
export class DocumentAddComponent implements OnInit {
  websiteId: string;
  document: Document;
  allStates: SelectItem[] = [];
  submitted = false;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.apiService.getStates().subscribe(states => {
      states.forEach(state => {
        this.allStates.push({ label: state, value: state });
      });
    });
    this.route.paramMap.subscribe(
      (params: ParamMap) => (this.websiteId = params.get('websiteId'))
    );
    this.document = new Document(
      '',
      '',
      '',
      '',
      new Date(),
      '',
      '',
      this.websiteId,
      '',
      '',
      []
    );
  }

  onSubmit() {
    this.submitted = true;
    this.apiService
      .createDocument(this.document)
      .subscribe(document =>
        this.router.navigate(['/website/' + this.websiteId])
      );
  }
}
