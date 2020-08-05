import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import {
  RoDetailComponent,
  RoDetailSortableHeaderDirective,
} from './ro-detail/ro-detail.component';
import {
  RoListComponent,
  NgbdSortableHeaderDirective,
} from './ro-list/ro-list.component';
import { RoDocumentDetailsComponent } from './ro-document-details/ro-document-details.component';
import { RoRoutingModule } from './reporting-obligations-routing.module';
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
@NgModule({
  declarations: [
    RoListComponent,
    RoDetailComponent,
    NgbdSortableHeaderDirective,
    RoDetailSortableHeaderDirective,
    RoDocumentDetailsComponent,
  ],
  imports: [
    SharedModule,
    ChipsModule,
    ToastModule,
    TooltipModule,
    OverlayPanelModule,
    ConfirmDialogModule,
    SharedModule,
    RoRoutingModule,
  ],
  providers: [
    ConfirmationService,
    { provide: NgbDateAdapter, useClass: NgbDateNativeAdapter },
  ],
})
export class ReportingObligationsModule {}
