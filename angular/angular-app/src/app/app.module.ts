import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';

import { fakeBackendProvider } from './helpers/fake-backend';
import { TokenInterceptor } from './helpers/token.interceptor';
import { ErrorInterceptor } from './helpers/error.interceptor';
import { HomeComponent } from './home-component/home.component';
import { LoginComponent } from './login-component/login.component';
import { RegisterComponent } from './register-component/register.component';
import { AlertComponent } from './alert-component/alert.component';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { WebsiteListComponent, WebsiteNgbdSortableHeaderDirective } from './website-list/website-list.component';
import { WebsiteDetailsComponent } from './website-details/website-details.component';
import {
  SolrFileListComponent,
  NgbdSortableHeaderDirective
} from './solrfile-list/solrfile-list.component';

import { SocialLoginModule, AuthServiceConfig } from 'angularx-social-login';
import { getAuthServiceConfigs } from './social-login.config';

import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

@NgModule({
  declarations: [
    AppComponent,
    WebsiteListComponent,
    WebsiteDetailsComponent,
    WebsiteNgbdSortableHeaderDirective,
    HomeComponent,
    LoginComponent,
    RegisterComponent,
    AlertComponent,
    SolrFileListComponent,
    NgbdSortableHeaderDirective
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    NgbModule,
    ReactiveFormsModule,
    FormsModule,
    HttpClientModule,
    SocialLoginModule,
    FontAwesomeModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
    { provide: AuthServiceConfig, useFactory: getAuthServiceConfigs }
    //fakeBackendProvider
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
