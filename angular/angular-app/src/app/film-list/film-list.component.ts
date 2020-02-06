import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { Film } from '../film';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-film-list',
  templateUrl: './film-list.component.html',
  styleUrls: ['./film-list.component.css']
})
export class FilmListComponent implements OnInit {
  films$: Observable<Film[]>;

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.getFilms();
  }

  public getFilms() {
    this.films$ = this.apiService.getFilms();
  }

}
