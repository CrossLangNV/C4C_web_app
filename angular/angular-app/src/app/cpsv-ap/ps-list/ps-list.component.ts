import {
  Component,
  OnInit
} from '@angular/core';
import {Router} from "@angular/router";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {DjangoUser} from "../../shared/models/django_user";

import * as demoData from '../demo_data.json';


@Component({
  selector: 'app-ps-list',
  templateUrl: './ps-list.component.html',
  styleUrls: ['./ps-list.component.css'],
})
export class PsListComponent implements OnInit {

  currentDjangoUser: DjangoUser;

  contentLoaded = true;

  collapsed: boolean = true;

  publicServices: any = (demoData as any).default;

  constructor(
    private router: Router,
    private authenticationService: AuthenticationService,
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );

    // Force login page when not authenticated
    if (this.currentDjangoUser == null) {
      this.router.navigate(['/login']);
    }
  }

  numSequence(n: number): Array<number> {
    return Array(n);
  }

  containsGroup(groups: Array<any>, groupName: String) {
    return groups.some(group => group.name == groupName);
  }
}
