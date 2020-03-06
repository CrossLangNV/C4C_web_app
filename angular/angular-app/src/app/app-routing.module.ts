import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { WebsiteListComponent } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import { FilmListComponent } from './film-list/film-list.component';

const routes: Routes = [
  { path: 'websites', component: WebsiteListComponent },
  { path: 'websites/:websiteId', component: WebsiteDetailsComponent },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes)
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }

