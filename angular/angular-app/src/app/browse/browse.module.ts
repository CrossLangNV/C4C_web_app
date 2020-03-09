import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import {
  WebsiteListComponent,
  WebsiteNgbdSortableHeaderDirective
} from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';

@NgModule({
  declarations: [
    WebsiteListComponent,
    WebsiteNgbdSortableHeaderDirective,
    WebsiteDetailsComponent
  ],
  imports: [SharedModule]
})
export class BrowseModule {}
