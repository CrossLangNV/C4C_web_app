import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class ConceptComment {
  public username: string;

  constructor(
    public id: string,
    public value: string,
    public conceptId: string,
    public userId: string,
    public createdAt: Date
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class ConceptCommentAdapter implements Adapter<ConceptComment> {
  adapt(item: any): ConceptComment {
    return new ConceptComment(
      item.id,
      item.value,
      item.concept,
      item.user,
      new Date(item.created_at)
    );
  }
  encode(conceptComment: ConceptComment): any {
    const stringDate = new Date(conceptComment.createdAt).toISOString();
    return {
      id: conceptComment.id,
      value: conceptComment.value,
      Concept: conceptComment.conceptId,
      concept: conceptComment.conceptId,
      user: conceptComment.userId,
      createdAt: stringDate,
    };
  }
}
