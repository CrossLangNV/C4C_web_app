import { Routes, RouterModule } from '@angular/router';

import { LoginComponent } from './shared/login-component/login.component';
import { AuthGuard } from './core/guards/auth.guard';
import {CpListComponent} from './cpsv-ap/cp-list/cp-list.component';
import {CpDetailComponent} from './cpsv-ap/cp-detail/cp-detail.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: '', redirectTo: '/validator', pathMatch: 'full' },
  {
    path: 'browse',
    loadChildren: () =>
      import('./browse/browse.module').then((m) => m.BrowseModule),
    canActivate: [AuthGuard],
  },
  {
    path: 'glossary',
    loadChildren: () =>
      import('./glossary/glossary.module').then((m) => m.GlossaryModule),
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
  {
    path: 'cpsv',
    loadChildren: () =>
      import('./cpsv-ap/cpsv-ap.module').then((m) => m.CPSVAPModule),
    canActivate: [AuthGuard],
  },
  {
    path: 'cp',
    component: CpListComponent,
    canActivate: [AuthGuard],
    children: [
      {
        path: ':cpId',
        component: CpDetailComponent,
      },
    ],
  },


  // otherwise redirect to home
  { path: '**', redirectTo: '/validator' },
];

export const AppRoutingModule = RouterModule.forRoot(routes);
