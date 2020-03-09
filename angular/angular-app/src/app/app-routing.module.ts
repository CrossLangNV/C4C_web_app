import { Routes, RouterModule } from '@angular/router';
import { WebsiteListComponent } from './browse/website-list/website-list.component';
import { WebsiteDetailsComponent } from './browse/website-details/website-details.component';


import { SolrFileListComponent } from './search/solrfile-list/solrfile-list.component';
import { LoginComponent } from './shared/login-component/login.component';
import { RegisterComponent } from './shared/register-component/register.component';
import { AuthGuard } from './core/guards/auth.guard';

const routes: Routes = [
  { path: '', component: SolrFileListComponent, canActivate: [AuthGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'websites', component: WebsiteListComponent },
  { path: 'websites/:websiteId', component: WebsiteDetailsComponent },

  // otherwise redirect to home
  { path: '**', redirectTo: '' }
];

export const AppRoutingModule = RouterModule.forRoot(routes);
