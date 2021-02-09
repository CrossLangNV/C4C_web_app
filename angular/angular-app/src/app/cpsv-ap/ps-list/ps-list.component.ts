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
import {Subject} from 'rxjs';
import {debounceTime, distinctUntilChanged} from 'rxjs/operators';
import {LazyLoadEvent} from 'primeng/api/lazyloadevent';


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
  offset = 0;
  rows = 5;
  previousPage: any;
  pageSize = 5;
  keyword = '';
  filterTag = '';
  sortBy = 'name';
  filterType = 'none'
  website = '';
  websites = [ { id: '', name: 'Website..' } ];
  searchTermChanged: Subject<string> = new Subject<string>();

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
    this.fetchWebsites();

    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.offset = 0;
        this.fetchPublicServices();
      });


  }

  fetchWebsites() {
    this.service.getWebsites().subscribe((websites) => {
      websites.forEach((website) => {
        this.websites.push({
          id: website.name.toLowerCase(),
          name: '..' + website.name.toUpperCase(),
        });
      });
    });
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
        this.offset,
        this.rows,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.sortBy,
        this.website,
      ).subscribe((results) => {
        this.publicServices = results.results;
        this.collectionSize = results.count;
    });
  }

  onSearch(keyword: string) {
    this.searchTermChanged.next(keyword);
  }

  filterResetPage() {
    this.offset = 0;
    this.fetchPublicServices();
    this.router.navigate(['/cpsv']);
  }


  fetchPublicServicesLazy(event: LazyLoadEvent) {
    let sortOrder = event.sortOrder == 1 ? '' : '-';
    this.sortBy = sortOrder + event.sortField;
    this.offset = event.first;
    this.rows = event.rows;
    this.fetchPublicServices();
  }
}
