import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor
} from '@angular/common/http';
import { Observable } from 'rxjs';

import { AuthenticationService } from '../authentication.service';

@Injectable()
export class TokenInterceptor implements HttpInterceptor {
  constructor(private authenticationService: AuthenticationService) {}

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // add authorization header with jwt token if available
    let currentDjangoToken = this.authenticationService.currentDjangoTokenValue;
    if (currentDjangoToken && currentDjangoToken.access_token) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${currentDjangoToken.access_token}`
        }
      });
    }

    return next.handle(request);
  }
}
