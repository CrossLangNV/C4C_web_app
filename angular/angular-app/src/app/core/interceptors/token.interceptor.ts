import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor
} from '@angular/common/http';
import { Observable } from 'rxjs';

import { AuthenticationService } from '../auth/authentication.service';

@Injectable()
export class TokenInterceptor implements HttpInterceptor {
  constructor(private authenticationService: AuthenticationService) {}

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // add authorization header with jwt token if available
    let currentDjangoUser = this.authenticationService.currentDjangoUserValue;
    if (currentDjangoUser && currentDjangoUser.access_token) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${currentDjangoUser.access_token}`
        }
      });
    }

    return next.handle(request);
  }
}
