import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class SolrDocument {
  constructor(
    public id: string,
    public title: string,
    public titlePrefix: string,
    public type: string,
    public date: Date,
    public acceptanceState: string,
    public url: string,
    public website: string,
    public summary: string,
    public content: string
  ) {}
}

@Injectable({
  providedIn: 'root'
})
export class SolrDocumentAdapter implements Adapter<SolrDocument> {
  adapt(item: any): SolrDocument {
    return new SolrDocument(
      item.id,
      item.title[0],
      item.title_prefix[0],
      item.type[0],
      new Date(item.date[0]),
      item.acceptance_state[0],
      item.url[0],
      item.website[0],
      item.summary ? item.summary[0] : '',
      item.content ? item.content[0] : ''
    );
  }
}
