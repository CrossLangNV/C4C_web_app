import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export interface DocumentResults {
  count: number;
  next: string;
  previous: string;
  results: Document[];
}
export class Document {
  constructor(
    public id: string,
    public title: string,
    public titlePrefix: string,
    public type: string,
    public date: Date,
    public acceptanceState: string,
    public acceptanceStateValue: string,
    public url: string,
    public website: string,
    public summary: string,
    public content: string,
    public attachmentIds: string[],
    public pull: boolean
  ) {}
}

@Injectable({
  providedIn: 'root',
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
      item.acceptance_state_value,
      item.url,
      item.website,
      item.summary,
      item.content,
      item.attachments,
      item.pull
    );
  }
  encode(document: Document): any {
    const stringDate = new Date(document.date).toISOString();
    return {
      id: document.id,
      title: document.title,
      title_prefix: document.titlePrefix,
      type: document.type,
      date: stringDate,
      acceptance_state: document.acceptanceState,
      acceptance_state_value: document.acceptanceStateValue,
      url: document.url,
      website: document.website,
      summary: document.summary,
      content: document.content,
      attachments: document.attachmentIds,
      pull: document.pull,
    };
  }
}
