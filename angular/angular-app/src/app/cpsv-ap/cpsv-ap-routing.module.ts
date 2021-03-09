import { Routes, RouterModule } from '@angular/router';
import { PsListComponent } from './ps-list/ps-list.component';
import {PsDetailComponent} from './ps-detail/ps-detail.component';
import {CpListComponent} from './cp-list/cp-list.component';
import {CpDetailComponent} from './cp-detail/cp-detail.component';

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
        ],
      },
      {
        path: 'cp',
        component: CpListComponent,
        children: [
          {
            path: ':cpId',
            component: CpDetailComponent,
          }
        ]
      },
    ],
  },
];

export const CPSVAPRoutingModule = RouterModule.forChild(routes);
