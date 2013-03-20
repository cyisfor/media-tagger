create or replace function wipe() RETURNS void AS
$$DECLARE
tablename text;
BEGIN
    for tablename in SELECT pg_tables.tablename FROM pg_tables where schemaname = 'public' LOOP
        EXECUTE 'DROP TABLE ' || tablename || ' CASCADE';
    END LOOP;
END$$ language 'plpgsql';

SELECT wipe();
