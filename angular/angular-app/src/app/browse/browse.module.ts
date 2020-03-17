import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import { DocumentDetailsComponent } from './document-details/document-details.component';
import { BrowseRoutingModule } from './browse-routing.module';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { SelectButtonModule } from 'primeng/selectbutton';
import { WebsiteAddComponent } from './website-add/website-add.component';
import { FormsModule }   from '@angular/forms';

@NgModule({
  declarations: [
    WebsiteListComponent,
    WebsiteDetailsComponent,
    DocumentDetailsComponent,
    WebsiteAddComponent
  ],
  imports: [
    SharedModule,
    BrowseRoutingModule,
    ScrollPanelModule,
    SelectButtonModule,
    FormsModule
  ]
})
export class BrowseModule {}
