import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentListComponent } from './document-list/document-list.component';
import { SharedModule } from '../shared/shared.module';
import { ValidatorRoutingModule } from './validator-routing.module';
import { DocumentValidateComponent } from './document-validate/document-validate.component';
import { TestcompoComponent } from './testcompo/testcompo.component';
import { SelectButtonModule } from 'primeng/selectbutton';

@NgModule({
  declarations: [
    DocumentListComponent,
    DocumentValidateComponent,
    TestcompoComponent,
  ],
  imports: [
    CommonModule,
    SharedModule,
    SelectButtonModule,
    ValidatorRoutingModule,
  ],
})
export class ValidatorModule {}
