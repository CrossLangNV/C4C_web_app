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
    public content: string,
    public attachmentIds: string[]
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
      item.content,
      item.attachments
    );
  }
  encode(document: Document): any {
    return {
      id: document.id,
      title: document.title,
      title_prefix: document.titlePrefix,
      type: document.type,
      date: document.date,
      acceptance_state: document.acceptanceState,
      url: document.url,
      website: document.website,
      summary: document.summary,
      content: document.content,
      attachments: document.attachmentIds
    };
  }
}
