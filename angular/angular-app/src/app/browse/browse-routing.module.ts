import { Routes, RouterModule } from '@angular/router';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import { DocumentDetailsComponent } from './document-details/document-details.component';

const routes: Routes = [
  { path: '', redirectTo: '/browse/website', pathMatch: 'full' },
  {
    path: 'website',
    data: {
      breadcrumb: 'Websites'
    },
    children: [
      {
        path: '',
        component: WebsiteListComponent
      },
      {
        path: ':websiteId',
        data: {
          breadcrumb: '',
          breadcrumbType: 'website'
        },
        children: [
          {
            path: '',
            component: WebsiteDetailsComponent
          },
          {
            path: 'document/:documentId',
            data: {
              breadcrumb: '',
              breadcrumbType: 'document'
            },
            component: DocumentDetailsComponent
          }
        ]
      }
    ]
  }
];

export const BrowseRoutingModule = RouterModule.forChild(routes);
