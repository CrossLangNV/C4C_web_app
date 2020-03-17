import { AppComponent } from './app.component';

import { CoreModule } from './core/core.module';
import { NgModule } from '@angular/core';
import { SearchModule } from './search/search.module';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SharedModule } from './shared/shared.module';
import { BrowseModule } from './browse/browse.module';
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [AppComponent],
  imports: [
    AppRoutingModule,
    SharedModule,
    BrowserModule,
    BrowserAnimationsModule,
    CoreModule,
    SearchModule,
    BrowseModule
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
