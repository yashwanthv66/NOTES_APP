create table users (
    id integer primary key autoincrement,
    username text unique not null,
    email text not null,
    password text not null
);

create table notes (
    id integer primary key autoincrement,
    title text not null,
    content text not null,
    created_at timestamp default current_timestamp,
    user_id integer,
    foreign key (user_id) references users(id)
);