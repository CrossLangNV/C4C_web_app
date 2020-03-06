import { Routes, RouterModule } from '@angular/router';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';


import { HomeComponent } from './home-component/home.component';
import { SolrFileListComponent } from './solrfile-list/solrfile-list.component';
import { LoginComponent } from './login-component/login.component';
import { RegisterComponent } from './register-component/register.component';
import { AuthGuard } from './helpers/auth.guard';

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
