import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import { DocumentDetailsComponent } from './document-details/document-details.component';

@NgModule({
  declarations: [WebsiteListComponent, WebsiteDetailsComponent, DocumentDetailsComponent],
  imports: [SharedModule]
})
export class BrowseModule {}
