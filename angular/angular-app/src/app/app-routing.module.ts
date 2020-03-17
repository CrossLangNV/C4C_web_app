import { Routes, RouterModule } from '@angular/router';

import { SolrFileListComponent } from './search/solrfile-list/solrfile-list.component';
import { LoginComponent } from './shared/login-component/login.component';
import { RegisterComponent } from './shared/register-component/register.component';
import { AuthGuard } from './core/guards/auth.guard';

const routes: Routes = [
  { path: '', component: SolrFileListComponent, canActivate: [AuthGuard] },
  { path: '', component: SolrFileListComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  {
    path: 'browse',
    loadChildren: () =>
      import('./browse/browse.module').then(m => m.BrowseModule)
  },

  // otherwise redirect to home
  { path: '**', redirectTo: '' }
];

export const AppRoutingModule = RouterModule.forRoot(routes);
