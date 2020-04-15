import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class Comment {
  public username: string;

  constructor(
    public id: string,
    public value: string,
    public documentId: string,
    public userId: string,
    public createdAt: Date
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class CommentAdapter implements Adapter<Comment> {
  adapt(item: any): Comment {
    return new Comment(
      item.id,
      item.value,
      item.document,
      item.user,
      new Date(item.created_at)
    );
  }
  encode(comment: Comment): any {
    const stringDate = new Date(comment.createdAt).toISOString();
    return {
      id: comment.id,
      value: comment.value,
      document: comment.documentId,
      user: comment.userId,
      createdAt: stringDate,
    };
  }
}
