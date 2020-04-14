import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class Comment {
  public username: string;

  constructor(
    public id: string,
    public value: string,
    public documentId: string,
    public userId: string
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class CommentAdapter implements Adapter<Comment> {
  adapt(item: any): Comment {
    return new Comment(item.id, item.value, item.document, item.user);
  }
  encode(comment: Comment): any {
    return {
      id: comment.id,
      value: comment.value,
      document: comment.documentId,
      user: comment.userId,
    };
  }
}
