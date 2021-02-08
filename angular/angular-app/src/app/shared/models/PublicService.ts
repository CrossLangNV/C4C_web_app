import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class PublicServiceResults {
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
    public results: PublicService[]
  ) {}
}

export class PublicService {
  constructor(
    public id: string,
    public name: string,
    public description: string,
    public identifier: string,
    public concepts: string[]
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class PublicServiceAdapter implements Adapter<PublicService> {
  adapt(item: any): PublicService {
    return new PublicService(
      item.id,
      item.name,
      item.description,
      item.identifier,
      item.concepts,
    );
  }
  encode(ps: PublicService): any {
    return {
      id: ps.id,
      name: ps.name,
      description: ps.description,
      identifier: ps.identifier,
      concepts: ps.concepts,
    };
  }
}
