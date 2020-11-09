import { Injectable } from '@angular/core';
import { Adapter } from './adapter';
import {Concept} from "./concept";

export class RoResults {
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
    public results: ReportingObligation[]
  ) {}
}

export class ReportingObligation {
  constructor(
    public id: string,
    public name: string,
    public definition: string,
    public documentIds: string[],
    public tags: string[],
    public commentIds: string[],
    public concept: string,
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class RoAdapter implements Adapter<ReportingObligation> {
  adapt(item: any): ReportingObligation {
    return new ReportingObligation(
      item.id,
      item.name,
      item.definition,
      item.documents,
      item.tags,
      item.comments,
      item.concept,
    );
  }
  encode(ro: ReportingObligation): any {
    return {
      id: ro.id,
      name: ro.name,
      definition: ro.definition,
      documents: ro.documentIds,
      tags: ro.tags,
      comments: ro.commentIds,
      concept: ro.concept,
    };
  }
}
