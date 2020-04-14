import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentListComponent } from './document-list/document-list.component';
import { SharedModule } from '../shared/shared.module';
import { ValidatorRoutingModule } from './validator-routing.module';
import { DocumentValidateComponent } from './document-validate/document-validate.component';
import { SelectButtonModule } from 'primeng/selectbutton';
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
    ValidatorRoutingModule,
  ],
})
export class ValidatorModule {}
