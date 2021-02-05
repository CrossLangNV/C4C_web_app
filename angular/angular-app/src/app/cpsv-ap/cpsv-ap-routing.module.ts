import { Routes, RouterModule } from '@angular/router';
import { PsListComponent } from './ps-list/ps-list.component';

const routes: Routes = [
  {
    path: 'ro',
    data: {
      breadcrumb: 'CPSV-AP',
    },
    children: [
      {
        path: '',
        component: PsListComponent,
        children: [
        ],
      },
    ],
  },
];

export const CPSVAPRoutingModule = RouterModule.forChild(routes);
