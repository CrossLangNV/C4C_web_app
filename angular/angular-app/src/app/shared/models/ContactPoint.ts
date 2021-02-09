import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class ContactPointResults {
  constructor(
    public count: number,
    public count_unvalidated: number,
    public count_total: number,
    public count_rejected: number,
    public count_validated: number,
    public count_autorejected: number,
    public count_autovalidated: number,
    public next: string,
    public previous: string,
    public results: ContactPoint[]
  ) {}
}

export class ContactPoint {
  constructor(
    public id: string,
    public identifier: string,
    public description: string,
    public pred: string,
    public opening_hours: string,
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class ContactPointAdapter implements Adapter<ContactPoint> {
  adapt(item: any): ContactPoint {
    return new ContactPoint(
      item.id,
      item.identifier,
      item.description,
      item.pred,
      item.opening_hours,
    );
  }
  encode(ps: ContactPoint): any {
    return {
      id: ps.id,
      identifier: ps.identifier,
      description: ps.description,
      pred: ps.pred,
      opening_hours: ps.opening_hours,
    };
  }
}
