CREATE OR REPLACE FUNCTION findTag(_name text) RETURNS INTEGER AS 
$$
DECLARE 
_id INTEGER;
BEGIN
    if _name IS NULL THEN
        RETURN NULL;
    END IF;
    LOOP
        SELECT tags.id INTO _id FROM tags WHERE name = _name;
        IF FOUND THEN
            RETURN _id;
        END IF;
        BEGIN
            INSERT INTO things DEFAULT VALUES RETURNING id INTO _id;
            INSERT INTO tags (id,name) VALUES (_id,_name);
        EXCEPTION
            WHEN unique_violation THEN
                -- do nothing
        END;
    END LOOP;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION connectOneWay(_thing1 INTEGER, _thing2 INTEGER) RETURNS void AS
$$
BEGIN
    --RAISE NOTICE 'trying % to %',_thing1,_thing2;
    UPDATE things SET neighbors = neighbors || _thing2 WHERE id = _thing1 AND NOT neighbors @> ARRAY[_thing2];
    --IF FOUND THEN
        --RAISE NOTICE 'connected % to %',_thing1,_thing2;
    --END IF;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION connect(_thing1 INTEGER, _thing2 INTEGER) RETURNS void AS
$$
BEGIN
    PERFORM connectOneWay(_thing1,_thing2);
    PERFORM connectOneWay(_thing2,_thing1);
END;
$$ LANGUAGE 'plpgsql';

--UPDATE things SET neighbors = neighbors || 281532::INTEGER WHERE id = 218508 AND NOT neighbors @>  ARRAY[281532::INTEGER];

--UPDATE things SET neighbors = neighbors || array(SELECT id FROM tags AS tagsinner WHERE tagsinner.name LIKE tags.name || ':%') FROM tags WHERE things.id = tags.id AND NOT tags.name LIKE '%:%';

SELECT count(*) FROM (SELECT 
    connect(tags.id,findTag(split_part(name,':',1))),
    connect(tags.id,findTag(split_part(name,':',2)))
    FROM (SELECT id,name FROM tags WHERE name LIKE '%:%' ORDER BY tags.id OFFSET 24000 LIMIT 4000) AS tags) AS foo;
