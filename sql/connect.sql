-- DROP FUNCTION connect(a INTEGER, b INTEGER);
-- DROP FUNCTION connectOne(a INTEGER, b INTEGER);
-- DROP FUNCTION connectMany(a INTEGER[], b INTEGER[]);

CREATE OR REPLACE FUNCTION connectOneToMany(a INTEGER, b INTEGER[]) RETURNS void AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(b)) where things.id = a;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION connectManyToOne(a INTEGER[], b INTEGER) RETURNS void AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = ANY(a);
END;
$$ language 'plpgsql';


CREATE OR REPLACE FUNCTION connectOne(a INTEGER, b INTEGER) RETURNS void AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = a;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION disconnect(a INTEGER, b INTEGER) RETURNS void AS $$
BEGIN
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT b) AS derp) WHERE id = a and neighbors @> ARRAY[b];
END;
$$ language 'plpgsql';
    
