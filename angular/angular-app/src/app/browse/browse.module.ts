import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import { DocumentDetailsComponent } from './document-details/document-details.component';
import { BrowseRoutingModule } from './browse-routing.module';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { SelectButtonModule } from 'primeng/selectbutton';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DropdownModule } from 'primeng/dropdown';
import { ConfirmationService } from 'primeng/api';
import { WebsiteAddComponent } from './website-add/website-add.component';
import { DocumentAddComponent } from './document-add/document-add.component';

@NgModule({
  declarations: [
    WebsiteListComponent,
    WebsiteDetailsComponent,
    DocumentDetailsComponent,
    WebsiteAddComponent,
    DocumentAddComponent
  ],
  imports: [
    SharedModule,
    BrowseRoutingModule,
    ScrollPanelModule,
    SelectButtonModule,
    ConfirmDialogModule,
    DropdownModule
  ],
  providers: [ConfirmationService]
})
export class BrowseModule {}
