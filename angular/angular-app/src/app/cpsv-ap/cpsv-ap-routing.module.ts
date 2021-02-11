import { Routes, RouterModule } from '@angular/router';
import { PsListComponent } from './ps-list/ps-list.component';
import {PsDetailComponent} from './ps-detail/ps-detail.component';

const routes: Routes = [
  {
    path: 'cpsv',
    data: {
      breadcrumb: 'CPSV-AP',
    },
    children: [
      {
        path: '',
        component: PsListComponent,
        children: [
          {
            path: ':psId',
            component: PsDetailComponent,
          },
          // {
          //   path: ':cpId',
          //   component: PsDetailComponent,
          // }
        ],
      },
    ],
  },
];

export const CPSVAPRoutingModule = RouterModule.forChild(routes);
