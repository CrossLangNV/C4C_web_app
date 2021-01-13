import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentListComponent } from './document-list/document-list.component';
import { SharedModule } from '../shared/shared.module';
import { ValidatorRoutingModule } from './validator-routing.module';
import { DocumentValidateComponent } from './document-validate/document-validate.component';
import { SelectButtonModule } from 'primeng/selectbutton';
import { ChipsModule } from 'primeng/chips';
import { InputSwitchModule } from 'primeng/inputswitch';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ChartModule } from 'primeng/chart';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { TruncatePipe } from '../shared/pipelines/truncate';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';
import { SliderModule } from 'primeng/slider';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { InputNumberModule } from 'primeng/inputnumber';
import { NgbDateAdapter, NgbDateNativeAdapter } from '@ng-bootstrap/ng-bootstrap';
import { NgbdSortableHeader } from './document-list/sortable.directive';
import { DropdownModule } from 'primeng/dropdown';
import { FieldsetModule } from 'primeng/fieldset';

@NgModule({
  declarations: [
    DocumentListComponent,
    NgbdSortableHeader,
    DocumentValidateComponent,
    TruncatePipe,
  ],
  imports: [
    CommonModule,
    SharedModule,
    SelectButtonModule,
    ChipsModule,
    InputSwitchModule,
    ToastModule,
    TooltipModule,
    ChartModule,
    OverlayPanelModule,
    ConfirmDialogModule,
    SliderModule,
    ScrollPanelModule,
    InputNumberModule,
    ValidatorRoutingModule,
    DropdownModule,
    FieldsetModule,
  ],
  providers: [
    ConfirmationService,
    { provide: NgbDateAdapter, useClass: NgbDateNativeAdapter }
  ]
})
export class ValidatorModule {}
