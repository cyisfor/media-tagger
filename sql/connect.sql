CREATE OR REPLACE FUNCTION connect(a bigint, b bigint) RETURNS void AS $$
BEGIN
    IF (SELECT count(id) FROM things WHERE id = a AND neighbors @> ARRAY[b]) = 0 THEN
        update things set neighbors = neighbors || b where things.id = a;
    END IF;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION disconnect(a bigint, b bigint) RETURNS void AS $$
BEGIN
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT b) AS derp) WHERE id = a and neighbors @> ARRAY[b];
END;
$$ language 'plpgsql';
    
