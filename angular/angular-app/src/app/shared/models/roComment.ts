import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class RoComment {
  public username: string;

  constructor(
    public id: string,
    public value: string,
    public roId: string,
    public userId: string,
    public createdAt: Date
  ) {}
}

@Injectable({
  providedIn: 'root',
})
export class RoCommentAdapter implements Adapter<RoComment> {
  adapt(item: any): RoComment {
    return new RoComment(
      item.id,
      item.value,
      item.reporting_obligation,
      item.user,
      new Date(item.created_at)
    );
  }

  encode(roComment: RoComment): any {
    const stringDate = new Date(roComment.createdAt).toISOString();
    return {
      id: roComment.id,
      value: roComment.value,
      reporting_obligation: roComment.roId,
      user: roComment.userId,
      createdAt: stringDate,
    };
  }
}
