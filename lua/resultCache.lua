-- SELECT id FROM -> CREATE TABLE FROM SELECT etc

local db = require('db')
local hash = require('hash')

db.setup("CREATE SCHEMA IF NOT EXISTS resultCache",
[[CREATE TABLE resultCache.queries(
        id SERIAL PRIMARY KEY,
        digest TEXT UNIQUE,
        created timestamptz DEFAULT clock_timestamp())]],
[[CREATE OR REPLACE FUNCTION resultCache.updateQuery(_digest text) RETURNS void AS
$$
BEGIN
    LOOP
        UPDATE resultCache.queries SET created = clock_timestamp() WHERE digest = _digest;
        IF found THEN
            RETURN;
        END IF;
        BEGIN
            INSERT INTO resultCache.queries (digest) VALUES (_digest);
        EXCEPTION
            WHEN unique_violation THEN
                -- do nothing
        END;
    END LOOP;
END;
$$ language 'plpgsql'
]],
[[CREATE OR REPLACE FUNCTION resultCache.expireQueries() RETURNS void AS
$$
DECLARE
_digest text;
BEGIN
    FOR _digest IN DELETE FROM resultCache.queries RETURNING digest LOOP
        BEGIN
            EXECUTE 'DROP TABLE resultCache."q' || _digest || '"';
        EXCEPTION
            WHEN undefined_table THEN
                -- do nothing
        END;
    END LOOP;
END;
$$ language 'plpgsql'
]],
[[CREATE OR REPLACE FUNCTION resultCache.expireQueriesTrigger() RETURNS trigger AS
$$
BEGIN
    PERFORM resultCache.expireQueries();
    RETURN OLD;
END;
$$ language 'plpgsql'
]],
[[CREATE TRIGGER expireTrigger AFTER INSERT OR UPDATE OR DELETE ON things
    EXECUTE PROCEDURE resultCache.expireQueriesTrigger()]])

return function(query, args)

    local name = hash()
    name.update(query)
    for arg in args do
        name.update(arg)
    end
    name = name.final()

    return db.transaction(function()
        ok,err = pcall(function()
            db.execute('CREATE TABLE resultCache."q'..name..'" AS '..query,unpack(args))
            db.execute('SELECT resultCache.updateQuery($1)',name)
        end)
        if not ok then
            if err:match('already exists') then
                db.retransaction()
                return db.execute('SELECT * FROM resultCache."q'..name..'"')
            else
                error(err)
            end
        end
    end)
end
