import {Component, OnInit, ViewEncapsulation} from '@angular/core';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ApiService } from 'src/app/core/services/api.service';
import { switchMap } from 'rxjs/operators';
import { Document } from 'src/app/shared/models/document';
import {ReportingObligation} from '../../shared/models/ro';

@Component({
  selector: 'app-ro-breakdown',
  templateUrl: './ro-breakdown.component.html',
  styleUrls: ['./ro-breakdown.component.css'],
  encapsulation: ViewEncapsulation.ShadowDom,

})
export class RoBreakdownComponent implements OnInit {
  content_html_ro: string;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService
  ) {
    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getReportingObligationsView(params.get('documentId'))
        )
      ).subscribe((response) => {
        console.log('what 2')
        this.content_html_ro = response
    });
  }

  ngOnInit(): void {
  }
}
