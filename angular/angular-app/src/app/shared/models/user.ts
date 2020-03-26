import { Injectable } from '@angular/core';
import { Adapter } from './adapter';

export class User {
  constructor(
    public id: number,
    public username: string,
    public password: string,
    public firstName: string,
    public lastName: string,
    public isSuperuser: boolean
  ) {}
}

@Injectable({
  providedIn: 'root'
})
export class UserAdapter implements Adapter<User> {
  adapt(item: any): User {
    return new User(
      item.id,
      item.username,
      item.password,
      item.first_name,
      item.last_name,
      item.is_superuser
    );
  }
  encode(user: User): any {
    return {
      id: user.id,
      username: user.username,
      password: user.password,
      first_name: user.firstName,
      last_name: user.lastName,
      is_superuser: user.isSuperuser
    };
  }
}
