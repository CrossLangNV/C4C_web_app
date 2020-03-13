import { Routes, RouterModule } from '@angular/router';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import { DocumentDetailsComponent } from './document-details/document-details.component';

const routes: Routes = [
  { path: '', redirectTo: '/browse/website', pathMatch: 'full' },
  {
    path: 'website',
    children: [
      {
        path: '',
        component: WebsiteListComponent
      },
      {
        path: ':websiteId',
        component: WebsiteDetailsComponent
      }
    ]
  },
  {
    path: 'document',
    children: [
      {
        path: ':documentId',
        component: DocumentDetailsComponent
      }
    ]
  }
];

export const BrowseRoutingModule = RouterModule.forChild(routes);
