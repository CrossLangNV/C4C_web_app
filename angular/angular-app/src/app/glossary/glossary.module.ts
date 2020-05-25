import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { ConceptListComponent } from './concept-list/concept-list.component';



@NgModule({
  declarations: [ConceptListComponent],
  imports: [
    SharedModule
  ]
})
export class GlossaryModule { }
