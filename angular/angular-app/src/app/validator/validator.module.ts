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

@NgModule({
  declarations: [
    DocumentListComponent,
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
    ValidatorRoutingModule,
  ],
})
export class ValidatorModule {}
