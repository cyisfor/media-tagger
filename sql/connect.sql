-- DROP FUNCTION connect(a bigint, b bigint);
-- DROP FUNCTION connectOne(a bigint, b bigint);
-- DROP FUNCTION connectMany(a bigint[], b bigint[]);

CREATE OR REPLACE FUNCTION connectOneToMany(a bigint, b bigint[]) RETURNS void AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(b)) where things.id = a;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION connectManyToOne(a bigint[], b bigint) RETURNS void AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = ANY(a);
END;
$$ language 'plpgsql';


CREATE OR REPLACE FUNCTION connectOne(a bigint, b bigint) RETURNS void AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = a;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION disconnect(a bigint, b bigint) RETURNS void AS $$
BEGIN
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT b) AS derp) WHERE id = a and neighbors @> ARRAY[b];
END;
$$ language 'plpgsql';
    
