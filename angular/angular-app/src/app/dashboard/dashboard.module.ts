import { NgModule } from '@angular/core';
import { UserListComponent } from './user-list/user-list.component';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { SharedModule } from '../shared/shared.module';
import { DocumentListComponent } from './document-list/document-list.component';
import { TableModule } from 'primeng/table';

@NgModule({
  declarations: [UserListComponent, DocumentListComponent],
  imports: [SharedModule, DashboardRoutingModule, TableModule]
})
export class DashboardModule {}
