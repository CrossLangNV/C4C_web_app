import {
  Component,
  OnInit
} from '@angular/core';
import {Router} from "@angular/router";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {DjangoUser} from "../../shared/models/django_user";

import * as demoData from '../demo_data.json';
import {PublicService} from '../../shared/models/PublicService';
import {ApiService} from '../../core/services/api.service';


@Component({
  selector: 'app-ps-list',
  templateUrl: './ps-list.component.html',
  styleUrls: ['./ps-list.component.css'],
})
export class PsListComponent implements OnInit {
  currentDjangoUser: DjangoUser;
  contentLoaded = true;
  collapsed = true;
  publicServices: PublicService[];

  selected: string;
  collectionSize = 0;
  selectedIndex: string = null;
  page = 1;
  previousPage: any;
  pageSize = 5;
  keyword = '';
  filterTag = '';
  sortBy = 'name';
  filterType = 'none'

  constructor(
    private router: Router,
    private authenticationService: AuthenticationService,
    private service: ApiService,
  ) {}

  ngOnInit() {
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );

    // Force login page when not authenticated
    if (this.currentDjangoUser == null) {
      this.router.navigate(['/login']);
    }

    this.fetchPublicServices();


  }

  numSequence(n: number): Array<number> {
    return Array(n);
  }

  containsGroup(groups: Array<any>, groupName: string) {
    return groups.some(group => group.name === groupName);
  }

  fetchPublicServices() {
    this.service
      .getRdfPublicServices(
        this.page,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.sortBy
      ).subscribe((results) => {
        this.publicServices = results.results;
        this.collectionSize = results.count;
    });
  }
}
