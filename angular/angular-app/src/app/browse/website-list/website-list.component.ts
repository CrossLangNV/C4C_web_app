import { Component, OnInit } from '@angular/core';
import { ApiServiceWebsites } from '../../core/services/api.service.websites';
import { Website } from '../../shared/models/website';

@Component({
  selector: 'app-website-list',
  templateUrl: './website-list.component.html',
  styleUrls: ['./website-list.component.css']
})
export class WebsiteListComponent implements OnInit {
  websites = [];

  constructor(private apiServiceWebsites: ApiServiceWebsites) {}

  ngOnInit() {
    this.apiServiceWebsites.getWebsites().subscribe(websites => {
      this.websites = websites as Website[];
    });
  }

  onDelete(id) {
    this.apiServiceWebsites.deleteWebsite(id).subscribe();
  }
}
