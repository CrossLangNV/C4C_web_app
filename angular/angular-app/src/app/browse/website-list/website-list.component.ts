import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Website } from '../../shared/models/website';

@Component({
  selector: 'app-website-list',
  templateUrl: './website-list.component.html',
  styleUrls: ['./website-list.component.css']
})
export class WebsiteListComponent implements OnInit {
  websites = [];

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.apiService.getWebsites().subscribe(websites => {
      this.websites = websites as Website[];
    });
  }

  onDelete(id) {
    this.apiService.deleteWebsite(id).subscribe();
  }
}
