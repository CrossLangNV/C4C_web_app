import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';

import { Document } from '../../shared/models/document';
import { SelectItem } from 'primeng/api/selectitem';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faCalendarAlt } from '@fortawesome/free-solid-svg-icons';
import { AcceptanceState } from 'src/app/shared/models/acceptanceState';

@Component({
  selector: 'app-document-add',
  templateUrl: './document-add.component.html',
  styleUrls: ['./document-add.component.css'],
})
export class DocumentAddComponent implements OnInit {
  websiteId: string;
  document: Document;
  acceptanceState: string;
  allStates: SelectItem[] = [];
  calendarIcon: IconDefinition;
  submitted = false;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.apiService.getStateValues().subscribe((states) => {
      states.forEach((state) => {
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
      '',
      this.websiteId,
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      [],
      [],
      [],
      '',
      '',
      [],
      []
    );
    this.calendarIcon = faCalendarAlt;
  }

  onSubmit() {
    this.submitted = true;
    this.apiService.createDocument(this.document).subscribe((document) => {
      console.log(document);
      this.apiService
        .updateState(
          new AcceptanceState(
            document.acceptanceState,
            document.id,
            '',
            this.acceptanceState
          )
        )
        .subscribe((state) =>
          this.router.navigate(['/website/' + this.websiteId])
        );
    });
  }
}
