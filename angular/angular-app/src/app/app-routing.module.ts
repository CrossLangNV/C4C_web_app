import { Routes, RouterModule } from '@angular/router';

import { SolrFileListComponent } from './search/solrfile-list/solrfile-list.component';
import { LoginComponent } from './shared/login-component/login.component';
import { AuthGuard } from './core/guards/auth.guard';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: 'browse',
    loadChildren: () =>
      import('./browse/browse.module').then((m) => m.BrowseModule),
    canActivate: [AuthGuard],
  },
  {
    path: 'search',
    component: SolrFileListComponent,
    canActivate: [AuthGuard],
  },
  {
    path: 'dashboard',
    loadChildren: () =>
      import('./dashboard/dashboard.module').then((m) => m.DashboardModule),
    canActivate: [AuthGuard],
  },
  {
    path: 'validator',
    loadChildren: () =>
      import('./validator/validator.module').then((m) => m.ValidatorModule),
    canActivate: [AuthGuard],
  },
  // otherwise redirect to home
  { path: '**', redirectTo: 'validator' },
];

export const AppRoutingModule = RouterModule.forRoot(routes);
