-- okay... so, create caching tables for individual tag queries
create table tagcache.t0_2_4 as select unnest(neighbors) from things where id = ANY(ARRAY[0,2,4]);
-- also insert into some list of cached tags
insert into tagcache.queries (tag,query) SELECT tag,(ARRAY[0,2,4]) FROM unnest(ARRAY[0,2,4]);
-- then when querying for +0, +2, +4 or -0, -2, -4, use tagcache.t0_2_4
-- or create it, if not in tagcache.queries
-- when changing a medium's tags, select by tag in tagcache.queries, and drop all the tables for that, then delete the row in tagcache.queries. regenerate on demand.


