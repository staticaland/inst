create table issues (
    id bigint primary key generated always as identity,
    title text not null,
    body text not null,
    labels text[] not null
);