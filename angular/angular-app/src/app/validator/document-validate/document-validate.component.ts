import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';
import { Observable } from 'rxjs';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import { SelectItem } from 'primeng/api/selectitem';
import { AcceptanceState } from 'src/app/shared/models/acceptanceState';

@Component({
  selector: 'app-document-validate',
  templateUrl: './document-validate.component.html',
  styleUrls: ['./document-validate.component.css'],
})
export class DocumentValidateComponent implements OnInit {
  document$: Observable<Document>;
  stateValues: SelectItem[] = [];
  acceptanceState: AcceptanceState;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {}

  ngOnInit() {
    this.acceptanceState = new AcceptanceState('', '', '', '');
    this.service.getStateValues().subscribe((states) => {
      states.forEach((state) => {
        this.stateValues.push({ label: state, value: state });
      });
    });
    this.document$ = this.route.paramMap.pipe(
      switchMap((params: ParamMap) =>
        this.service.getDocument(params.get('documentId'))
      )
    );
  }

  onStateChange(event) {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getDocument(params.get('documentId'))
        )
      )
      .subscribe((document) => {
        // FIXME: can we abract the the acceptanceState.id  via the API (should not be know externally ?)
        this.acceptanceState.id = document.acceptanceState;
        this.acceptanceState.value = event.value;
        this.acceptanceState.documentId = document.id;
        this.service.updateState(this.acceptanceState).subscribe();
      });
  }
}
