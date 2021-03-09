import { Component, OnInit } from '@angular/core';
import {DjangoUser} from '../../shared/models/django_user';
import {RdfFilter} from '../../shared/models/rdfFilter';
import {Subject} from 'rxjs';
import {MenuItem} from 'primeng/api';
import {IconDefinition} from '@fortawesome/fontawesome-svg-core';
import {faStopCircle} from '@fortawesome/free-solid-svg-icons';
import {Router} from '@angular/router';
import {AuthenticationService} from '../../core/auth/authentication.service';
import {ApiService} from '../../core/services/api.service';
import {debounceTime, distinctUntilChanged} from 'rxjs/operators';
import {LazyLoadEvent} from 'primeng/api/lazyloadevent';
import {TabMenu} from 'primeng/tabmenu';
import {ContactPoint} from '../../shared/models/ContactPoint';

@Component({
  selector: 'app-cp-list',
  templateUrl: './cp-list.component.html',
  styleUrls: ['./cp-list.component.css']
})
export class CpListComponent implements OnInit {

  currentDjangoUser: DjangoUser;
  contentLoaded = false;
  collapsed = true;
  contactPoints: ContactPoint[];

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

    this.fetchWebsites();
    this.fetchAvailableFilters();

    this.searchTermChanged
      .pipe(debounceTime(600), distinctUntilChanged())
      .subscribe((model) => {
        this.keyword = model;
        this.offset = 0;
        this.fetchContactPoints();
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

  fetchContactPoints() {
    this.checkFilters();
    this.service
      .getRdfContactPoints(
        this.offset,
        this.rows,
        this.keyword,
        this.filterTag,
        this.filterType,
        this.sortBy,
        this.website,
        this.selectedTags
      ).subscribe((results) => {
      this.contactPoints = results.results;
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
    this.fetchContactPoints()
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
    this.fetchContactPoints();
    this.router.navigate(['/cp']);
  }

  fetchContactPointsLazy(event: LazyLoadEvent) {
    const sortOrder = event.sortOrder === 1 ? '' : '-';
    this.sortBy = sortOrder + event.sortField;
    this.offset = event.first;
    this.rows = event.rows;
    this.fetchContactPoints();
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
      .fetchDropdowns('cp')
      .subscribe((results) => {
        this.availableItems = results
        this.contentLoaded = true;
      })
  }

  getPlaceholder(filter: RdfFilter) {
    return this.service.rdf_get_name_of_entity('cp', filter)
  }

  search(filter: RdfFilter, event) {
    this.service.fetchDropdownFilters('cp', filter, event.query, this.selectedTags).subscribe(data => {
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
    this.fetchContactPoints()
  }

}
