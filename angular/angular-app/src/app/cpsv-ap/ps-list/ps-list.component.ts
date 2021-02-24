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
import {TabMenu, TabMenuModule} from 'primeng/tabmenu';
import {MenuItem} from 'primeng/api';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {faStopCircle} from '@fortawesome/free-solid-svg-icons';
import {RdfFilter} from '../../shared/models/rdfFilter';


@Component({
  selector: 'app-ps-list',
  templateUrl: './ps-list.component.html',
  styleUrls: ['./ps-list.component.css'],
})
export class PsListComponent implements OnInit {
  currentDjangoUser: DjangoUser;
  contentLoaded = false;
  collapsed = true;
  publicServices: PublicService[];

  availableItems: RdfFilter[]
  availableItemsQuery: Map<string, string>;
  selectedTags: Map<string, Array<string>>;
  suggestions: string[];

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

  items: MenuItem[];
  activeItem: MenuItem;
  resetIcon: IconDefinition = faStopCircle;
  filterActive = false;

  psActive = true;
  cpActive = false;


  constructor(
    private router: Router,
    private authenticationService: AuthenticationService,
    private service: ApiService,
  ) {}

  ngOnInit() {
    this.availableItemsQuery = new Map<string, string>();
    this.selectedTags = new Map<string, Array<string>>();

    this.authenticationService.currentDjangoUser.subscribe(
      (x) => (this.currentDjangoUser = x)
    );

    // Force login page when not authenticated
    if (this.currentDjangoUser == null) {
      this.router.navigate(['/login']);
    }

    this.items = [
      {label: 'Public Services', icon: 'pi pi-fw pi-home'},
      {label: 'Contact Points', icon: 'pi pi-fw pi-id-card'},
    ];
    this.activeItem = this.items[0];

    this.fetchPublicServices();
    this.fetchWebsites();
    this.fetchAvailableFilters();

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
    this.checkFilters();
    this.service
      .getRdfPublicServices(
        this.offset,
        this.rows,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.sortBy,
        this.website,
        this.selectedTags
      ).subscribe((results) => {
        this.publicServices = results.results;
        this.collectionSize = results.count;
    });
  }

  resetFilters() {
    this.keyword = '';
    this.filterTag = '';
    this.filterType = '';
    this.website = '';
    this.availableItems = [];
    this.availableItemsQuery.clear();
    this.selectedTags.clear();
    this.filterResetPage();
    this.fetchPublicServices()
  }

  checkFilters() {
    this.filterActive =
      this.keyword.length > 0 ||
      this.filterTag.length > 0 ||
      this.filterType !== '' ||
      this.website !== '';
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
    const sortOrder = event.sortOrder === 1 ? '' : '-';
    this.sortBy = sortOrder + event.sortField;
    this.offset = event.first;
    this.rows = event.rows;
    this.fetchPublicServices();
  }

  activateMenu(tab: TabMenu) {
    // this.activeItem = tab.activeItem;
    // this.collectionSize = 0;

    if (tab.activeItem === this.items[0]) {
      this.router.navigate(['/cpsv']);
    } else {
      this.router.navigate(['/cp']);
      // this.fetchContactPoints();
      // this.psActive = false;
      // this.cpActive = true;
    }
  }

  setIndex(index) {
    this.selectedIndex = index;
  }

  fetchAvailableFilters() {
    this.service
      .fetchDropdowns('ps')
      .subscribe((results) => {
        this.availableItems = results
        this.contentLoaded = true;
      })
  }

  getPlaceholder(filter: RdfFilter) {
    return this.service.rdf_get_name_of_entity('ps', filter)
  }

  search(filter: RdfFilter, event) {
    this.service.fetchDropdownFilters('ps', filter, event.query, this.selectedTags).subscribe(data => {
      this.suggestions = data;

      if (event.query === '') {
        this.availableItemsQuery.delete(filter.toString())
      } else {
        this.availableItemsQuery.set(filter.toString(), event.value)
      }
      this.filterResetPage();
    })
  }

  onChangeFilter(filter: RdfFilter, event, action) {
    const filterKey = filter.toString()
    const previousValues = this.selectedTags.get(filterKey)
    const values = []

    if (action === 'add') {
      if (previousValues) {
        previousValues.forEach(key => {
          values.push(key)
        })
      }

      if (!(values.includes(event.label))) {
        values.push(event.label)
      }

      this.selectedTags.set(filterKey, values)
    } else {
      previousValues.pop()
      // Check if it happens to be completely empty now
      if (previousValues.length === 0) {
        // this.selectedTags.set(filterKey, null)
        this.selectedTags.delete(filterKey)
      } else {
        this.selectedTags.set(filterKey, previousValues)
      }
    }
    this.fetchPublicServices()
  }
}
