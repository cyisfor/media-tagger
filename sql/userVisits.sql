CREATE TABLE uzerVisits (
        id SERIAL PRIMARY KEY,
        uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE,
        media INTEGER REFERENCES media(id) ON DELETE CASCADE,
        UNIQUE(uzer,media))
---
CREATE OR REPLACE FUNCITON uzerVisitsInsert(_uzer INTEGER, _media INTEGER) RETURNS VOID AS
$$
BEGIN
    INSERT INTO uzerVisits (uzer,media) VALUES (_uzer,_media);
EXCEPTION WHEN unique_violation THEN
    -- whatever
END;
$$ LANGUAGE plpgsql
