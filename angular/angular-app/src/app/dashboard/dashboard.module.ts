import { NgModule } from '@angular/core';
import { UserListComponent } from './user-list/user-list.component';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { SharedModule } from '../shared/shared.module';
import { DocumentListComponent } from './document-list/document-list.component';
import { TableModule } from 'primeng/table';
import { NgbdSortableHeaderDirective } from './document-list/document-list.component';
@NgModule({
  declarations: [
    UserListComponent,
    DocumentListComponent,
    NgbdSortableHeaderDirective,
  ],
  imports: [SharedModule, DashboardRoutingModule, TableModule],
})
export class DashboardModule {}
