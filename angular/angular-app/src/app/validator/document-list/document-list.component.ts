import { Component, OnInit, QueryList, ViewChildren } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import {
  faMicrochip,
  faSort,
  faSortDown,
  faSortUp,
  faStar,
  faStopCircle,
  faSyncAlt,
  faUserAlt,
  faUserLock
} from '@fortawesome/free-solid-svg-icons';
import { Observable, Subject } from 'rxjs';
import { AuthenticationService } from 'src/app/core/auth/authentication.service';
import { ApiService } from 'src/app/core/services/api.service';
import { DocumentService } from 'src/app/core/services/document.service';
import { DjangoUser } from 'src/app/shared/models/django_user';
import {Document, DocumentResults} from 'src/app/shared/models/document';
import { Tag } from 'src/app/shared/models/tag';
import { NgbdSortableHeader, SortEvent } from './sortable.directive';
import {DropdownOption} from '../../shared/models/DropdownOption';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css'],
})
export class DocumentListComponent implements OnInit {
  @ViewChildren(NgbdSortableHeader) headers: QueryList<NgbdSortableHeader>;

  documentResults$: Observable<DocumentResults>;
  selectedId: number;
  data1: any;
  data2: any;
  options1 = {
    title: {
      display: true,
      text: 'Auto classification',
      fontSize: 16,
    },
    legend: {
      position: 'bottom',
    },
  };
  options2 = {
    title: {
      display: true,
      text: 'Human classification',
      fontSize: 16,
    },
    legend: {
      position: 'bottom',
    },
  };
  pageSize = 5;
  filterActive = false;
  stats = {
    classifiedSize: 0,
    classifiedPercent: 0,
    unvalidatedSize: 0,
    unvalidatedPercent: 0,
    acceptedSize: 0,
    acceptedPercent: 0,
    rejectedSize: 0,
    rejectedPercent: 0,
    autoClassifiedSize: 0,
    autoClassifiedPercent: 0,
    autoUnvalidatedSize: 0,
    autoUnvalidatedPercent: 0,
    autoAcceptedSize: 0,
    autoAcceptedPercent: 0,
    autoRejectedSize: 0,
    autoRejectedPercent: 0,
    totalDocuments: 0,
  };
  userIcon: IconDefinition;
  userLockIcon: IconDefinition;
  chipIcon: IconDefinition;
  reloadIcon: IconDefinition = faSyncAlt;
  resetIcon: IconDefinition = faStopCircle;
  titleSortIcon: IconDefinition = faSort;
  bookmarkIcon: IconDefinition = faStar;
  dateSortIcon: IconDefinition = faSortDown;
  statesSortIcon: IconDefinition = faSort;
  filters = [
    { id: '', name: 'Filter..' },
    { id: 'unvalidated', name: '..Unvalidated' },
    { id: 'accepted', name: '..Accepted' },
    { id: 'rejected', name: '..Rejected' },
  ];
  websites = [ { id: '', name: 'Website..' } ];
  currentDjangoUser: DjangoUser;
  selectedIndex: string = null;

  celexOptions: DropdownOption[];
  typeOptions: DropdownOption[];
  statusOptions: DropdownOption[];
  eliOptions: DropdownOption[];
  authorOptions: DropdownOption[];
  effectDateOptions: DropdownOption[];

  selectedCelex: string;
  selectedType: string;
  selectedStatus: string;
  selectedEli: string;
  selectedAuthor: string;
  selectedEffectDate: string;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: ApiService,
    public documentService: DocumentService,
    private authenticationService: AuthenticationService
  ) {}

  fetchDocuments() {
    this.checkFilters();
    // Fetch documents list
    this.documentResults$ = this.documentService.documentResults$;
    // Fetch statistics
    this.service.getDocumentStats().subscribe((result) => {
      // Human
      this.stats.unvalidatedSize = result.count_unvalidated;
      this.stats.acceptedSize = result.count_accepted;
      this.stats.rejectedSize = result.count_rejected;
      this.stats.classifiedSize = this.stats.acceptedSize + this.stats.rejectedSize;

      this.stats.classifiedPercent =
        (this.stats.classifiedSize / this.stats.totalDocuments) * 100;
      this.stats.classifiedPercent =
        Math.round((this.stats.classifiedPercent + Number.EPSILON) * 100) / 100;

      this.stats.unvalidatedPercent =
        (this.stats.unvalidatedSize / (this.stats.classifiedSize + this.stats.unvalidatedSize)) * 100;
      this.stats.unvalidatedPercent =
        Math.round((this.stats.unvalidatedPercent + Number.EPSILON) * 100) /
        100;

      this.stats.acceptedPercent =
        (this.stats.acceptedSize / (this.stats.classifiedSize + this.stats.unvalidatedSize)) * 100;
      this.stats.acceptedPercent =
        Math.round((this.stats.acceptedPercent + Number.EPSILON) * 100) / 100;

      this.stats.rejectedPercent =
        (this.stats.rejectedSize / (this.stats.classifiedSize + this.stats.unvalidatedSize)) * 100;
      this.stats.rejectedPercent =
        Math.round((this.stats.rejectedPercent + Number.EPSILON) * 100) / 100;

      // Classifier
      this.stats.autoUnvalidatedSize = result.count_autounvalidated;
      this.stats.autoAcceptedSize = result.count_autoaccepted;
      this.stats.autoRejectedSize = result.count_autorejected;
      this.stats.autoClassifiedSize = this.stats.autoAcceptedSize + this.stats.autoRejectedSize;

      this.stats.autoClassifiedPercent = (this.stats.autoClassifiedSize / this.stats.totalDocuments) * 100;
      this.stats.autoClassifiedPercent =
        Math.round((this.stats.autoClassifiedPercent + Number.EPSILON) * 100) /
        100;

      this.stats.autoUnvalidatedPercent =
        (this.stats.autoUnvalidatedSize / (this.stats.autoClassifiedSize + this.stats.autoUnvalidatedSize)) * 100;
      this.stats.autoUnvalidatedPercent =
        Math.round((this.stats.autoUnvalidatedPercent + Number.EPSILON) * 100) /
        100;

      this.stats.autoAcceptedPercent =
        (this.stats.autoAcceptedSize / (this.stats.autoClassifiedSize + this.stats.autoUnvalidatedSize)) * 100;
      this.stats.autoAcceptedPercent =
        Math.round((this.stats.autoAcceptedPercent + Number.EPSILON) * 100) /
        100;

      this.stats.autoRejectedPercent =
        (this.stats.autoRejectedSize / (this.stats.autoClassifiedSize + this.stats.autoUnvalidatedSize)) * 100;
      this.stats.autoRejectedPercent =
        Math.round((this.stats.autoRejectedPercent + Number.EPSILON) * 100) /
        100;
    });
  }
  ngOnInit() {
    this.userIcon = faUserAlt;
    this.userLockIcon = faUserLock;
    this.chipIcon = faMicrochip;
    this.authenticationService.currentDjangoUser.subscribe(
      (x) => {
        this.currentDjangoUser = x;
        this.documentService.username=x.username;
      }
    );
    this.service.getWebsites().subscribe((websites) => {
      websites.forEach((website) => {
        this.websites.push({
          id: website.name.toLowerCase(),
          name: '..' + website.name.toUpperCase(),
        });
      });
      this.websites.sort((a, b) => (a.name > b.name) ? 1 : -1);
    });
    this.documentService.total_documents().subscribe((value: number) => {
      this.stats.totalDocuments = value;
    });
    this.fetchDocuments();
    this.service.messageSource.asObservable().subscribe((value: string) => {
      if (value === 'refresh') {
        // trigger documentService to update the list
        this.documentService.page = this.documentService.page;
      }
    });

    // Fill dropdowns
    this.fetchCelexOptions();
    this.fetchTypeOptions();
    this.fetchStatusOptions();
    this.fetchEliOptions();
    this.fetchAuthorOptions();
    this.fetchEffectDateOptions();
  }

  onSort({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach((header) => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    // sorting documents, default date descending (-date)
    if (direction === '') {
      this.documentService.sortBy = '-date';
      this.titleSortIcon = faSort;
      this.dateSortIcon = faSortDown;
      this.statesSortIcon = faSort;
    } else {
      let sortBy = direction === 'asc' ? '' : '-';
      if (column === 'states') {
        column = 'acceptance_state_max_probability';
      }
      sortBy += column;
      this.documentService.sortBy = sortBy;
      const sortIcon = direction === 'asc' ? faSortUp : faSortDown;
      if (column === 'title') {
        this.titleSortIcon = sortIcon;
        this.dateSortIcon = faSort;
        this.statesSortIcon = faSort;
      } else if (column === 'date') {
        this.dateSortIcon = sortIcon;
        this.titleSortIcon = faSort;
        this.statesSortIcon = faSort;
      } else {
        this.statesSortIcon = sortIcon;
        this.titleSortIcon = faSort;
        this.dateSortIcon = faSort;
      }
    }
  }

  onAddTag(event, tags, documentId) {
    const newTag = new Tag('', event.value, documentId);
    this.service.addTag(newTag).subscribe((addedTag) => {
      // primeng automatically adds the string value first, delete this as workaround
      // see: https://github.com/primefaces/primeng/issues/3419
      tags.splice(-1, 1);
      // now add the tag object
      tags.push(addedTag);
    });
  }

  onRemoveTag(event) {
    this.service.deleteTag(event.value.id).subscribe();
  }

  onClickTag(event) {
    this.documentService.filterTag = event.value.value;
  }

  filterResetPage() {
    this.documentService.page = 1;
    this.router.navigate(['/validator']);
  }

  onPageChange() {
    this.router.navigate(['/validator']);
  }

  setIndex(index: string) {
    this.selectedIndex = index;
  }

  checkFilters() {
    this.filterActive =
      this.documentService.searchTerm.length > 0 ||
      this.documentService.filterTag.length > 0 ||
      this.documentService.showOnlyOwn ||
      this.documentService.filterType !== 'none' ||
      this.documentService.website !== 'none' ||
      this.documentService.celex !== 'none' ||
      this.documentService.type !== 'none' ||
      this.documentService.status !== 'none' ||
      this.documentService.eli !== 'none' ||
      this.documentService.author !== 'none' ||
      this.documentService.date_of_effect !== 'none';
  }

  resetFilters() {
    this.documentService.searchTerm = '';
    this.documentService.filterTag = '';
    this.documentService.showOnlyOwn = false;
    this.documentService.filterType = '';
    this.documentService.website = '';
    this.documentService.celex = '';
    this.documentService.type = '';
    this.documentService.status = '';
    this.documentService.eli = '';
    this.documentService.author = '';
    this.documentService.date_of_effect = '';
    this.resetDropdowns();
    this.router.navigate(['/validator']);
  }

  updateChart1(event: Event) {
    console.log('UPDATECHART1');
    console.log(this.stats);
    this.data1 = {
      labels: ['Unvalidated', 'Accepted', 'Rejected'],
      datasets: [
        {
          data: [
            this.stats.autoUnvalidatedPercent,
            this.stats.autoAcceptedPercent,
            this.stats.autoRejectedPercent,
          ],
          backgroundColor: ['#36A2EB', '#28A745', '#F47677'],
          hoverBackgroundColor: ['#36A2EB', '#28A745', '#F47677'],
        },
      ],
    };
  }

  updateChart2(event: Event) {
    console.log('UPDATECHART2');
    console.log(this.stats);
    this.data2 = {
      labels: ['Unvalidated', 'Accepted', 'Rejected'],
      datasets: [
        {
          data: [
            this.stats.unvalidatedPercent,
            this.stats.acceptedPercent,
            this.stats.rejectedPercent,
          ],
          backgroundColor: ['#36A2EB', '#28A745', '#F47677'],
          hoverBackgroundColor: ['#36A2EB', '#28A745', '#F47677'],
        },
      ],
    };
  }

  containsGroup(groups: Array<any>, groupName: String) {
    return groups.some(group => group.name == groupName);
  }

  onAddBookmark(document: Document) {
    this.service.addBookmark(this.currentDjangoUser, document).subscribe((dc) => {
     document.bookmark = true
    });
  }

  onRemoveBookmark(document: Document) {
    this.service.removeBookmark(document).subscribe((dc) => {
      // this.document.bookmark = false;
      document.bookmark = false
    });
  }

  fetchCelexOptions() {
    this.service.fetchCelexOptions().subscribe((res) => {
      this.celexOptions = res
    })
  }

  fetchTypeOptions() {
    this.service.fetchTypeOptions().subscribe((res) => {
      this.typeOptions = res
    })
  }

  fetchStatusOptions() {
    this.service.fetchStatusOptions().subscribe((res) => {
      this.statusOptions = res
    })
  }

  fetchEliOptions() {
    this.service.fetchEliOptions().subscribe((res) => {
      this.eliOptions = res
    })
  }

  fetchAuthorOptions() {
    this.service.fetchAuthorOptions().subscribe((res) => {
      this.authorOptions = res
    })
  }

  fetchEffectDateOptions() {
    this.service.fetchEffectDateOptions().subscribe((res) => {
      this.effectDateOptions = res
    })
  }

  onQuery(type, keyword) {
    let hasMatched = true;
    switch (type) {
      case 'celex':
        this.documentService.celex = keyword.code;
        break
      case 'type':
        this.documentService.type = keyword.code;
        break
      case 'status':
        this.documentService.status = keyword.code;
        break
      case 'eli':
        this.documentService.eli = keyword.code;
        break
      case 'author':
        this.documentService.author = keyword.code;
        break
      case 'date_of_effect':
        this.documentService.date_of_effect = keyword.code;
        break
      default:
        hasMatched = false;
    }
    // Because typescript has no 'finally' statement..
    if (hasMatched) {
      this.filterResetPage();
    }
  }

  resetDropdowns() {
    this.selectedCelex = '';
    this.selectedType = '';
    this.selectedStatus = '';
    this.selectedEli = '';
    this.selectedAuthor = '';
    this.selectedEffectDate = '';
  }
}
