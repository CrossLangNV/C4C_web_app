import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RoBreakdownComponent } from './ro-breakdown.component';

describe('RoBreakdownComponent', () => {
  let component: RoBreakdownComponent;
  let fixture: ComponentFixture<RoBreakdownComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RoBreakdownComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RoBreakdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
