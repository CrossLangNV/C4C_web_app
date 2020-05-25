import { Component, OnInit } from '@angular/core';
import { ApiService } from 'src/app/core/services/api.service';
import { Concept } from 'src/app/shared/models/concept';

@Component({
  selector: 'app-concept-list',
  templateUrl: './concept-list.component.html',
  styleUrls: ['./concept-list.component.css']
})
export class ConceptListComponent implements OnInit {
  concepts = [];

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.apiService.getConcepts().subscribe(concepts => {
      this.concepts = concepts as Concept[];
    });
  }

}
