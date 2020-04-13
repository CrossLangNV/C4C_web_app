import { Routes, RouterModule } from '@angular/router';
import { DocumentListComponent } from './document-list/document-list.component';
import { DocumentValidateComponent } from './document-validate/document-validate.component';
import { TestcompoComponent } from './testcompo/testcompo.component';

const routes: Routes = [
  {
    path: '',
    data: {
      breadcrumb: 'Validator',
    },
    children: [
      {
        path: '',
        component: DocumentListComponent,
      },
      // {
      //   path: '',
      //   component: DocumentValidateComponent,
      //   outlet: 'secondary',
      // },
      // {
      //   path: 'document/:documentId',
      //   component: DocumentListComponent,
      // },
      // {
      //   path: 'doc/:documentid',
      //   component: DocumentValidateComponent,
      //   outlet: 'secondary',
      // },
    ],
  },
  {
    path: 'document/:documentId',
    component: DocumentValidateComponent,
    outlet: 'secondary',
  },
];

export const ValidatorRoutingModule = RouterModule.forChild(routes);
