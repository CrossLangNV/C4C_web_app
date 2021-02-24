import { Component, OnInit, Directive, Input, Output, EventEmitter, ViewChildren, QueryList } from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { switchMap } from 'rxjs/operators';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {DjangoUser} from '../../shared/models/django_user';
import {AuthenticationService} from '../../core/auth/authentication.service';
import {MessageService, ConfirmationService} from 'primeng/api';
import {ApiAdminService} from '../../core/services/api.admin.service';
import {PublicService} from '../../shared/models/PublicService';
import {ContactPoint} from '../../shared/models/ContactPoint';

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
export class PsDetailSortableHeaderDirective {
  @Input() sortable: string;
  @Input() direction: SortDirection = '';
  @Output() sortDetail = new EventEmitter<SortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.sortDetail.emit({ column: this.sortable, direction: this.direction });
  }
}

@Component({
  selector: 'app-ps-detail',
  templateUrl: './ps-detail.component.html',
  styleUrls: ['./ps-detail.component.css'],
  providers: [MessageService]
})
export class PsDetailComponent implements OnInit {
  @ViewChildren(PsDetailSortableHeaderDirective) headers: QueryList<
    PsDetailSortableHeaderDirective
  >;
  ps: PublicService;

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
          this.service.getPs(params.get('psId'))
        )
      )
      .subscribe((ps) => {
        this.ps = ps;
      })
  }
}
