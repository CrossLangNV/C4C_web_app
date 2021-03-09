import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import {
  PsListComponent,
} from './ps-list/ps-list.component';
import { CPSVAPRoutingModule } from './cpsv-ap-routing.module';
import { ChipsModule } from 'primeng/chips';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';
import {
  NgbDateAdapter,
  NgbDateNativeAdapter,
} from '@ng-bootstrap/ng-bootstrap';
import { DropdownModule } from 'primeng/dropdown';
import { FieldsetModule } from 'primeng/fieldset';
import {PanelModule} from 'primeng/panel';
import {MenuModule} from 'primeng/menu';
import { SelectButtonModule } from 'primeng/selectbutton';
import {NgxSkeletonLoaderModule} from 'ngx-skeleton-loader';
import { DirectivesModule } from '../directives/directives.module';
import {TableModule} from 'primeng/table';
import {InputSwitchModule} from 'primeng/inputswitch';
import {TabMenuModule} from 'primeng/tabmenu';
import {PsDetailComponent} from './ps-detail/ps-detail.component';
import {AutoCompleteModule} from 'primeng/autocomplete';
import { CpListComponent } from './cp-list/cp-list.component';
import { CpDetailComponent } from './cp-detail/cp-detail.component';
import {InputTextareaModule} from 'primeng/inputtextarea';

@NgModule({
    declarations: [
        PsListComponent,
        PsDetailComponent,
        CpListComponent,
        CpDetailComponent,
    ],
  imports: [
    SharedModule,
    ChipsModule,
    ToastModule,
    TooltipModule,
    OverlayPanelModule,
    ConfirmDialogModule,
    SharedModule,
    CPSVAPRoutingModule,
    DropdownModule,
    FieldsetModule,
    PanelModule,
    MenuModule,
    SelectButtonModule,
    NgxSkeletonLoaderModule.forRoot(),
    DirectivesModule,
    TableModule,
    InputSwitchModule,
    TabMenuModule,
    AutoCompleteModule,
    InputTextareaModule,
  ],
  providers: [
    ConfirmationService,
    { provide: NgbDateAdapter, useClass: NgbDateNativeAdapter },
  ],
})
export class CPSVAPModule {}
