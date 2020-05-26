import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class Concept {
  constructor(
    public id: string,
    public name: string,
    public definition: string,
    public documentIds: string[]
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class ConceptAdapter implements Adapter<Concept> {
  adapt(item: any): Concept {
    return new Concept(item.id, item.name, item.definition, item.documents);
  }
  encode(concept: Concept): any {
    return {
      id: concept.id,
      name: concept.name,
      definition: concept.definition,
      documents: concept.documentIds,
    };
  }
}
