import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class Website {
  constructor(
    public id: string,
    public name: string,
    public url: string,
    public content: string,
    public documentIds: string[]
  ) {}
}

@Injectable({
  providedIn: 'root'
})
export class WebsiteAdapter implements Adapter<Website> {
  adapt(item: any): Website {
    return new Website(
      item.id,
      item.name,
      item.url,
      item.content,
      item.documents
    );
  }
}
