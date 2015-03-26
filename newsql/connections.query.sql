CREATE OR REPLACE FUNCTION followConnections(source integer) RETURNS SETOF(int) AS $$

WITH RECURSIVE previous(source,dest,depth,path,cycle) AS (
    SELECT source,dest,
            1,ARRAY[c.id],false FROM
        connections c INNER JOIN tags ON tags.id = c.source
            WHERE tags.name = 'flash'
    UNION ALL
    SELECT c.source,c.dest,
            p.depth+1,p.path || c.id, c.id = ANY(p.path)
        FROM connections c, previous p
            WHERE c.source = p.dest
            AND NOT p.cycle AND p.depth < 3
)
SELECT source,(select name from tags where id = source),array_agg(dest) from previous group by source;
