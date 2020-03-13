import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';

@NgModule({
  declarations: [WebsiteListComponent, WebsiteDetailsComponent],
  imports: [SharedModule]
})
export class BrowseModule {}
