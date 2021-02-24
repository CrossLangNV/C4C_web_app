import {Component, Directive, EventEmitter, Input, OnInit, Output, QueryList, ViewChildren} from '@angular/core';
import {PublicService} from '../../shared/models/PublicService';
import {ContactPoint} from '../../shared/models/ContactPoint';
import {IconDefinition} from '@fortawesome/fontawesome-svg-core';
import {DjangoUser} from '../../shared/models/django_user';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {ApiService} from '../../core/services/api.service';
import {AuthenticationService} from '../../core/auth/authentication.service';
import {ConfirmationService, MessageService} from 'primeng/api';
import {ApiAdminService} from '../../core/services/api.admin.service';
import {switchMap} from 'rxjs/operators';
export type SortDirection = 'asc' | 'desc' | '';

const rotate: { [key: string]: SortDirection } = {
  asc: 'desc',
  desc: '',
  '': 'asc',
};

export interface SortEvent {
  column: string;
  direction: SortDirection;
}

@Directive({
  selector: 'th[sortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()',
  },
})
export class CpDetailSortableHeaderDirective {
  @Input() sortable: string;
  @Input() direction: SortDirection = '';
  @Output() sortDetail = new EventEmitter<SortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.sortDetail.emit({ column: this.sortable, direction: this.direction });
  }
}
@Component({
  selector: 'app-cp-detail',
  templateUrl: './cp-detail.component.html',
  styleUrls: ['./cp-detail.component.css'],
  providers: [MessageService],
})
export class CpDetailComponent implements OnInit {

  @ViewChildren(CpDetailSortableHeaderDirective) headers: QueryList<
    CpDetailSortableHeaderDirective
    >;
  cp: ContactPoint;
  deleteIcon: IconDefinition;
  currentDjangoUser: DjangoUser;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private authenticationService: AuthenticationService,
    private service: ApiService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private adminService: ApiAdminService,
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );

    this.route.paramMap
      .pipe(
        switchMap((params: ParamMap) =>
          this.service.getCp(params.get('cpId'))
        )
      )
      .subscribe((cp) => {
        this.cp = cp;
      })
  }
}
