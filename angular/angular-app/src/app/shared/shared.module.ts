import { NgModule } from '@angular/core';
import { HomeComponent } from './home-component/home.component';
import { LoginComponent } from './login-component/login.component';
import { RegisterComponent } from './register-component/register.component';
import { AlertComponent } from './alert-component/alert.component';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { BreadcrumbComponent } from './breadcrumb-component/breadcrumb.component';
import { BreadcrumbModule } from 'primeng/breadcrumb';

@NgModule({
  declarations: [
    HomeComponent,
    LoginComponent,
    RegisterComponent,
    AlertComponent,
    BreadcrumbComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    NgbModule,
    ReactiveFormsModule,
    FormsModule,
    FontAwesomeModule,
    BreadcrumbModule
  ],
  exports: [
    CommonModule,
    RouterModule,
    HomeComponent,
    LoginComponent,
    RegisterComponent,
    AlertComponent,
    FormsModule,
    ReactiveFormsModule,
    NgbModule,
    FontAwesomeModule,
    BreadcrumbModule,
    BreadcrumbComponent
  ]
})
export class SharedModule {}
