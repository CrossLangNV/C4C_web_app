import { Injectable } from '@angular/core';
import { Adapter } from './adapter';
import { Attachment } from './attachment';
import { Concept } from './concept';

export interface DocumentResults {
  count: number;
  count_total: number;
  count_unvalidated: number;
  count_rejected: number;
  count_validated: number;
  count_autorejected: number;
  count_autovalidated: number;
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
    public websiteName: string,
    public summary: string,
    public content: string,
    public various: string,
    public celex: string,
    public eli: string,
    public status: string,
    public author: string,
    public attachments: Attachment[],
    public commentIds: string[],
    public tags: string[],
    public bookmark: boolean,
    public consolidatedVersions: string,
    public file: File,
    public fileUrl: string,
    public occurrance: Concept[],
    public definition: Concept[]
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
      item.website_name,
      item.summary,
      item.content,
      item.various,
      item.celex,
      item.eli,
      item.status,
      item.author,
      item.attachments,
      item.comments,
      item.tags,
      item.bookmark,
      item.consolidated_versions,
      item.file,
      item.file_url,
      item.occurrance,
      item.definition
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
      website_name: document.websiteName,
      summary: document.summary,
      content: document.content,
      various: document.various,
      celex: document.celex,
      eli: document.eli,
      status: document.status,
      author: document.author,
      attachments: document.attachments,
      comments: document.commentIds,
      tags: document.tags,
      bookmark: document.bookmark,
      consolidatedVersions: document.consolidatedVersions,
      file: document.file,
      file_url: document.fileUrl,
      occurrance: document.occurrance,
      definition: document.definition
    };
  }
}
