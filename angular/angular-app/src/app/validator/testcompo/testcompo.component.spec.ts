import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TestcompoComponent } from './testcompo.component';

describe('TestcompoComponent', () => {
  let component: TestcompoComponent;
  let fixture: ComponentFixture<TestcompoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TestcompoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestcompoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
