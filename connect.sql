CREATE OR REPLACE FUNCTION connect(a bigint, b bigint) RETURNS void AS $$
BEGIN
    IF (SELECT count(id) FROM things WHERE id = a AND neighbors @> ARRAY[b]) = 0 THEN
        update things set neighbors = neighbors || b where things.id = a;
    END IF;
    IF (SELECT count(id) FROM things WHERE id = b AND neighbors @> ARRAY[a]) = 0 THEN
        update things set neighbors = neighbors || a where things.id = b;
    END IF;
END;
$$ language 'plpgsql';

CREATE FUNCTION disconnect(a bigint, b bigint) RETURNS void AS $$
BEGIN
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT a) AS derp) WHERE id = b;
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT b) AS derp) WHERE id = a;
END;
$$ language 'plpgsql';
    
