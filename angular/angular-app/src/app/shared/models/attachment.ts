import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class Attachment {
  constructor(
    public id: string,
    public file: string,
    public url: string,
    public documentId: string
  ) {}
}

@Injectable({
  providedIn: 'root'
})
export class AttachmentAdapter implements Adapter<Attachment> {
  adapt(item: any): Attachment {
    return new Attachment(
      item.id,
      item.file,
      item.url,
      item.document
    );
  }
}