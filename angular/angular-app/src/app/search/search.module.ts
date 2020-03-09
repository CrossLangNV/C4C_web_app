import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { SolrFileListComponent, NgbdSortableHeaderDirective } from './solrfile-list/solrfile-list.component';



@NgModule({
  declarations: [
    SolrFileListComponent,
    NgbdSortableHeaderDirective
  ],
  imports: [
    SharedModule
  ]
})
export class SearchModule { }
