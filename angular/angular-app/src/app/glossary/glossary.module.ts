import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { ConceptListComponent } from './concept-list/concept-list.component';
import { ConceptDetailComponent } from './concept-detail/concept-detail.component';
import { GlossaryRoutingModule } from './glossary-routing.module';



@NgModule({
  declarations: [ConceptListComponent, ConceptDetailComponent],
  imports: [
    SharedModule,
    GlossaryRoutingModule
  ]
})
export class GlossaryModule { }
