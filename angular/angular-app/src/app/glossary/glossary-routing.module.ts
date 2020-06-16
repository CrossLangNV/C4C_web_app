import { Routes, RouterModule } from '@angular/router';
import { ConceptListComponent } from './concept-list/concept-list.component';
import { ConceptDetailComponent } from './concept-detail/concept-detail.component';

const routes: Routes = [
  {
    path: '',
    data: {
      breadcrumb: 'Concepts',
    },
    children: [
      {
        path: '',
        component: ConceptListComponent,
      },
    ],
  },
  {
    path: 'concept/:conceptId',
    component: ConceptDetailComponent,
    outlet: 'secondary',
  },
];

export const GlossaryRoutingModule = RouterModule.forChild(routes);
