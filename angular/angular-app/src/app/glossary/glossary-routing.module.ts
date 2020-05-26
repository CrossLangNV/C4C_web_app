import { Routes, RouterModule } from '@angular/router';
import { ConceptListComponent } from './concept-list/concept-list.component';
import { ConceptDetailComponent } from './concept-detail/concept-detail.component';

const routes: Routes = [
  { path: 'glossary', redirectTo: '/glossary/concepts', pathMatch: 'full' },
  {
    path: 'concepts',
    data: {
      breadcrumb: 'Concepts',
    },
    children: [
      {
        path: '',
        component: ConceptListComponent,
      },
      {
        path: ':conceptId',
        data: {
          breadcrumb: '',
        },
        children: [
          {
            path: '',
            component: ConceptDetailComponent,
          },
        ],
      },
    ],
  },
];

export const GlossaryRoutingModule = RouterModule.forChild(routes);
