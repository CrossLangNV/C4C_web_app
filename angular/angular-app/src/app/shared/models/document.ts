import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class Document {
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
export class DocumentAdapter implements Adapter<Document> {
  adapt(item: any): Document {
    return new Document(
      item.id,
      item.title,
      item.title_prefix,
      item.type,
      new Date(item.date),
      item.acceptance_state,
      item.url,
      item.website,
      item.summary,
      item.content
    );
  }
}
