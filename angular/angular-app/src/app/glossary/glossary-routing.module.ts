import { Routes, RouterModule } from '@angular/router';
import { ConceptListComponent } from './concept-list/concept-list.component';
import { ConceptDetailComponent } from './concept-detail/concept-detail.component';

const routes: Routes = [
  {
    path: 'glossary',
    data: {
      breadcrumb: 'Concepts',
    },
    children: [
      {
        path: '',
        component: ConceptListComponent,
        children: [
          {
            path: ':conceptId',
            component: ConceptDetailComponent,
          },
        ],
      },
    ],
  },
];

export const GlossaryRoutingModule = RouterModule.forChild(routes);
