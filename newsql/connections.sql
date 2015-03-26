create table connections (
    id BIGSERIAL PRIMARY KEY,
    source BIGINT REFERENCES things(id),
    dest BIGINT REFERENCES things(id),
    UNIQUE(source,dest));

CREATE OR REPLACE FUNCTION connect(_source bigint,_dest bigint) RETURNS boolean AS $$
BEGIN
    INSERT INTO connections (source,dest) VALUES (_source,_dest);
    RETURN TRUE;
EXCEPTION
    WHEN unique_violation THEN
        RETURN FALSE;
END
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION migrateConnections() RETURNS VOID AS $$
DECLARE
_id bigint;
_neighbors bigint[];
_neighbor bigint;
_counter int;
BEGIN
    _counter := 1;
    FOR _id,_neighbors IN SELECT id,neighbors FROM things LOOP
        FOR _neighbor IN SELECT n FROM 
                unnest(_neighbors) as n INNER JOIN things ON n = things.id LOOP
            IF connect(_neighbor,_id) THEN
                _counter := _counter + 1;
            END IF;
            IF _counter % 100 = 0 THEN
                RAISE NOTICE 'Connected %', _counter;
--                IF _counter % 10000 = 0 THEN
--                    RETURN;
--                END IF;
            END IF;
        END LOOP;
    END LOOP;
END
$$ language 'plpgsql';

SELECT migrateConnections();

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
            AND NOT p.cycle AND p.depth < 4
)
SELECT source,array_agg(dest) from previous group by source;

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
            AND NOT p.cycle AND p.depth < 4
)
SELECT source,array_agg(dest) from previous group by source;
