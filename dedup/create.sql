CREATE FUNCTION hammingfast(bigint, bigint) RETURNS real
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/pg_similarity', 'hammingfast';
