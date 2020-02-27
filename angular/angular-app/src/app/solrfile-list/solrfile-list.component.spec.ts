import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SolrFileListComponent } from './solrfile-list.component';

describe('SolrFileListComponent', () => {
  let component: SolrFileListComponent;
  let fixture: ComponentFixture<SolrFileListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SolrFileListComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SolrFileListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
