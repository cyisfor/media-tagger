--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: resultcache; Type: SCHEMA; Schema: -; Owner: user
--

CREATE SCHEMA resultcache;


ALTER SCHEMA resultcache OWNER TO "user";

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: first_last_agg; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS first_last_agg WITH SCHEMA public;


--
-- Name: EXTENSION first_last_agg; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION first_last_agg IS 'first() and last() aggregate functions';


SET search_path = public, pg_catalog;

--
-- Name: advanceoffsets(); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION advanceoffsets() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE queryOffsets SET ooffset = ooffset + 1;
END
$$;


ALTER FUNCTION public.advanceoffsets() OWNER TO "user";

--
-- Name: clearneighbors(); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION clearneighbors() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT OLD.id) where neighbors @> ARRAY[OLD.id];
        RETURN OLD;
    END;
$$;


ALTER FUNCTION public.clearneighbors() OWNER TO "user";

--
-- Name: connect(INTEGER, INTEGER); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connect(_source INTEGER, _dest INTEGER) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO connections (source,dest) VALUES (_source,_dest);
    RETURN TRUE;
EXCEPTION
    WHEN unique_violation THEN
        RETURN FALSE;
END
$$;


ALTER FUNCTION public.connect(_source INTEGER, _dest INTEGER) OWNER TO "user";

--
-- Name: connectmanytoone(INTEGER[], INTEGER); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connectmanytoone(a INTEGER[], b INTEGER) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = ANY(a);
END;
$$;


ALTER FUNCTION public.connectmanytoone(a INTEGER[], b INTEGER) OWNER TO "user";

--
-- Name: connectone(INTEGER, INTEGER); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connectone(a INTEGER, b INTEGER) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = a;
END;
$$;


ALTER FUNCTION public.connectone(a INTEGER, b INTEGER) OWNER TO "user";

--
-- Name: connectonetomany(INTEGER, INTEGER[]); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connectonetomany(a INTEGER, b INTEGER[]) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(b)) where things.id = a;
END;
$$;


ALTER FUNCTION public.connectonetomany(a INTEGER, b INTEGER[]) OWNER TO "user";

--
-- Name: disconnect(INTEGER, INTEGER); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION disconnect(a INTEGER, b INTEGER) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT b) AS derp) WHERE id = a and neighbors @> ARRAY[b];
END;
$$;


ALTER FUNCTION public.disconnect(a INTEGER, b INTEGER) OWNER TO "user";

--
-- Name: findtag(text); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION findtag(_name text) RETURNS INTEGER
    LANGUAGE plpgsql
    AS $$
DECLARE 
_id INTEGER;
BEGIN
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
$$;


ALTER FUNCTION public.findtag(_name text) OWNER TO "user";

--
-- Name: findurisource(text); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION findurisource(_uri text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
_id int;
BEGIN
    LOOP
        -- first try to find it
        SELECT id INTO _id FROM urisources WHERE uri = _uri;
        IF found THEN
            return _id;
        END IF;
        BEGIN
            INSERT INTO sources DEFAULT VALUES RETURNING id INTO _id;
            INSERT INTO urisources (id,uri) VALUES (_id,_uri);
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing we can just find it now.
        END;
    END LOOP;
END;
$$;


ALTER FUNCTION public.findurisource(_uri text) OWNER TO "user";

--
-- Name: listmedia(INTEGER[], INTEGER[], integer, integer); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION listmedia(_posi INTEGER[], _nega INTEGER[], _offset integer, _limit integer) RETURNS SETOF INTEGER
    LANGUAGE plpgsql
    AS $$
DECLARE
_ioffset int;
_ooffset int;
_maxoffset int;
_oldbottom int;
_page int DEFAULT 0;
_base RECORD;
_derp INTEGER[];
BEGIN
    -- get the real offset in media by the 
    _ioffset := _offset;
    SELECT count(id) INTO _maxoffset FROM things;
    SELECT ooffset,ioffset INTO _ooffset,_oldbottom FROM queryOffsets WHERE posi = _posi AND nega = _nega AND ioffset <= _ioffset ORDER BY ioffset LIMIT 1;
    IF found THEN
        _ioffset := _ioffset - _oldbottom;
    ELSE
        _ooffset := 0;
    END IF;
    LOOP
        IF _ooffset > _maxoffset THEN
            RETURN;
        END IF;
        FOR _base IN SELECT id FROM media ORDER BY added DESC OFFSET _ooffset LIMIT 10000 LOOP
            _ooffset := _ooffset + 1;
            WITH RECURSIVE getneighb(id, depth) AS ( 
                    SELECT id, 1 FROM things WHERE id = _base.id 
                    UNION ALL SELECT things.id,depth+1 FROM getneighb, 
                            things INNER JOIN tags ON things.id = tags.id
                        WHERE things.neighbors @> ARRAY[getneighb.id]
                        AND depth < 3)
                SELECT array_agg(id) INTO _derp FROM getneighb; 
            RAISE NOTICE 'neighbors % %',_derp,_nega;
            IF (NOT (_nega && _derp)) AND (_posi <@ _derp) THEN
                -- blah blah insert a new query offset for this query
                LOOP
                    SELECT ooffset INTO _ooffset FROM queryOffsets WHERE posi = _posi ANd nega = _nega AND ioffset = _ioffset;
                    IF found THEN
                        EXIT;
                    ELSE
                        BEGIN
                            INSERT INTO queryOffsets (posi,nega,ioffset,ooffset) VALUES (_posi,_nega,_ioffset,_ooffset);
                            EXIT;
                        EXCEPTION WHEN unique_violation THEN
                            -- do nothing, try the update again
                        END;
                    END IF;
                END LOOP;

                RETURN NEXT _base.id;
                _ioffset := _ioffset + 1;
                _limit := _limit - 1;
                IF _limit <= 0 THEN
                    RETURN;
                END IF;
            END IF;
        END LOOP;
        if _ooffset = 0 THEN
            RETURN;
        END IF;
    END LOOP;
END;
$$;


ALTER FUNCTION public.listmedia(_posi INTEGER[], _nega INTEGER[], _offset integer, _limit integer) OWNER TO "user";

--
-- Name: mergeadded(INTEGER, INTEGER); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION mergeadded(_a INTEGER, _b INTEGER) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
_aadd timestamptz;
_badd timestamptz;
BEGIN
    _aadd := COALESCE(added,modified,created,now()) FROM media WHERE id = _a;
    _badd := COALESCE(added,modified,created,now()) FROM media WHERE id = _b;
    UPDATE media SET added = NULL WHERE id = _b;
    UPDATE media SET added = GREATEST(_aadd,_badd) WHERE id = _a;
END
$$;


ALTER FUNCTION public.mergeadded(_a INTEGER, _b INTEGER) OWNER TO "user";

--
-- Name: mergesources(integer, integer); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION mergesources(_dest integer, _loser integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF _dest != _loser THEN
        UPDATE media SET sources = array(SELECT unnest(sources) UNION SELECT _dest EXCEPT SELECT _loser) WHERE sources @> ARRAY[_loser];
        UPDATE comics SET source = _dest WHERE source = _loser;
        DELETE FROM sources WHERE id = _loser;
    END IF;
END;
$$;


ALTER FUNCTION public.mergesources(_dest integer, _loser integer) OWNER TO "user";

--
-- Name: mergesources(integer, integer, text); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION mergesources(_dest integer, _loser integer, _uri text) RETURNS text
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF _dest != _loser THEN
        UPDATE media SET sources = array(SELECT unnest(sources) UNION SELECT _dest EXCEPT SELECT _loser) WHERE sources @> ARRAY[_loser];
        UPDATE comics SET source = _dest WHERE source = _loser;
        DELETE FROM sources WHERE id = _loser;
        UPDATE urisources SET uri = _uri WHERE id = _dest;
        RETURN _dest || ' yay ' || _uri;
    END IF;
    UPDATE urisources SET uri = _uri WHERE id = _dest;
    RETURN 'nope ' || _uri;
END;
$$;


ALTER FUNCTION public.mergesources(_dest integer, _loser integer, _uri text) OWNER TO "user";

--
-- Name: migrateconnections(); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION migrateconnections() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
_id INTEGER;
_neighbors INTEGER[];
_neighbor INTEGER;
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
$$;


ALTER FUNCTION public.migrateconnections() OWNER TO "user";

--
-- Name: neighbor_nodupes(); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION neighbor_nodupes() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS(select id FROM neighbors WHERE red = NEW.red and blue = NEW.blue) THEN RETURN NULL; END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.neighbor_nodupes() OWNER TO "user";

--
-- Name: outneighbors(); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION outneighbors() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
_id int;
_offset int;
_affected int;
_c NO SCROLL CURSOR FOR 
    insert into neighbors (red,blue) select id,unnest(array(select unnest from unnest(neighbors) where EXISTS(select id from things where id = unnest.unnest))) from things RETURNING id;
BEGIN
    raise NOTICE 'beginning';
    _offset := 0;
    FOR _id IN _c LOOP
        raise NOTICE 'Did %', _offset;
        _offset = _offset + 1;
    END LOOP;
END;
$$;


ALTER FUNCTION public.outneighbors() OWNER TO "user";

--
-- Name: setcomicpage(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION setcomicpage(_medium integer, _comic integer, _which integer) RETURNS void
    LANGUAGE plpgsql
    AS $$

BEGIN                                                  
     LOOP                                               
         -- first try to update the key 
         UPDATE comicPage set medium = _medium where comic = _comic and which = _which;
         IF found THEN                                  
             RETURN;                                    
         END IF;                                        
         -- not there, so try to insert the key         
         -- if someone else inserts the same key concurrently
         -- we could get a unique-key failure           
         BEGIN                                          
             INSERT INTO comicPage(medium,comic,which) VALUES (_medium,_comic,_which);
             RETURN;                                    
         EXCEPTION WHEN unique_violation THEN           
             -- Do nothing, and loop to try the UPDATE again.
         END;                                           
     END LOOP;                                          
END;
$$;


ALTER FUNCTION public.setcomicpage(_medium integer, _comic integer, _which integer) OWNER TO "user";

--
-- Name: wipe(); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION wipe() RETURNS void
    LANGUAGE plpgsql
    AS $$DECLARE
tablename text;
BEGIN
    for tablename in SELECT pg_tables.tablename FROM pg_tables where schemaname = 'public' LOOP
        EXECUTE 'DROP TABLE ' || tablename || ' CASCADE';
    END LOOP;
END$$;


ALTER FUNCTION public.wipe() OWNER TO "user";

SET search_path = resultcache, pg_catalog;

--
-- Name: expirequeries(); Type: FUNCTION; Schema: resultcache; Owner: user
--

CREATE FUNCTION expirequeries() RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION resultcache.expirequeries() OWNER TO "user";

--
-- Name: expirequeriestrigger(); Type: FUNCTION; Schema: resultcache; Owner: user
--

CREATE FUNCTION expirequeriestrigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM resultCache.expireQueries();
    RETURN OLD;
END;
$$;


ALTER FUNCTION resultcache.expirequeriestrigger() OWNER TO "user";

--
-- Name: updatequery(text); Type: FUNCTION; Schema: resultcache; Owner: user
--

CREATE FUNCTION updatequery(_digest text) RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION resultcache.updatequery(_digest text) OWNER TO "user";

SET search_path = public, pg_catalog;

--
-- Name: english_ispell; Type: TEXT SEARCH DICTIONARY; Schema: public; Owner: user
--

CREATE TEXT SEARCH DICTIONARY english_ispell (
    TEMPLATE = pg_catalog.ispell,
    dictfile = 'english', afffile = 'english', stopwords = 'english' );


ALTER TEXT SEARCH DICTIONARY public.english_ispell OWNER TO "user";

--
-- Name: pg; Type: TEXT SEARCH CONFIGURATION; Schema: public; Owner: user
--

CREATE TEXT SEARCH CONFIGURATION pg (
    PARSER = pg_catalog."default" );

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR numword WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR email WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR url WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR host WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR version WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR hword_numpart WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR numhword WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR url_path WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR file WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR "int" WITH simple;

ALTER TEXT SEARCH CONFIGURATION pg
    ADD MAPPING FOR uint WITH simple;


ALTER TEXT SEARCH CONFIGURATION public.pg OWNER TO "user";

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: badfiles; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE badfiles (
    path text NOT NULL
);


ALTER TABLE public.badfiles OWNER TO "user";

--
-- Name: blacklist; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE blacklist (
    id integer NOT NULL,
    hash character varying(28),
    reason text
);


ALTER TABLE public.blacklist OWNER TO "user";

--
-- Name: blacklist_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE blacklist_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.blacklist_id_seq OWNER TO "user";

--
-- Name: blacklist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE blacklist_id_seq OWNED BY blacklist.id;


--
-- Name: comicpage; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE comicpage (
    id integer NOT NULL,
    comic integer,
    which integer,
    medium integer
);


ALTER TABLE public.comicpage OWNER TO "user";

--
-- Name: comicpage_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE comicpage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.comicpage_id_seq OWNER TO "user";

--
-- Name: comicpage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE comicpage_id_seq OWNED BY comicpage.id;


--
-- Name: comics_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE comics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.comics_id_seq OWNER TO "user";

--
-- Name: comics; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE comics (
    id integer DEFAULT nextval('comics_id_seq'::regclass) NOT NULL,
    title text,
    description text,
    added timestamp with time zone DEFAULT clock_timestamp(),
    source integer
);


ALTER TABLE public.comics OWNER TO "user";

--
-- Name: connections; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE connections (
    id INTEGER NOT NULL,
    source INTEGER,
    dest INTEGER
);


ALTER TABLE public.connections OWNER TO "user";

--
-- Name: connections_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE connections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.connections_id_seq OWNER TO "user";

--
-- Name: connections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE connections_id_seq OWNED BY connections.id;


--
-- Name: derp; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE derp (
    id integer,
    hash character varying(28),
    inferior boolean
);


ALTER TABLE public.derp OWNER TO "user";

--
-- Name: desktops; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE desktops (
    id INTEGER NOT NULL,
    selected timestamp with time zone DEFAULT clock_timestamp() NOT NULL
);


ALTER TABLE public.desktops OWNER TO "user";

--
-- Name: dupes; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE dupes (
    id integer NOT NULL,
    medium INTEGER,
    hash character varying(28),
    inferior boolean DEFAULT false
);


ALTER TABLE public.dupes OWNER TO "user";

--
-- Name: dupes_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE dupes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dupes_id_seq OWNER TO "user";

--
-- Name: dupes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE dupes_id_seq OWNED BY dupes.id;


--
-- Name: filesources; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE filesources (
    id integer NOT NULL,
    path text
);


ALTER TABLE public.filesources OWNER TO "user";

--
-- Name: images; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE images (
    id INTEGER NOT NULL,
    animated boolean,
    width integer,
    height integer,
    ratio real
);


ALTER TABLE public.images OWNER TO "user";

--
-- Name: media; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE media (
    id INTEGER NOT NULL,
    name text,
    hash character(28),
    created timestamp with time zone,
    added timestamp with time zone DEFAULT clock_timestamp(),
    size integer,
    type text,
    md5 character(32),
    thumbnailed timestamp with time zone,
    sources integer[],
    modified timestamp with time zone DEFAULT clock_timestamp(),
    phash uuid
);


ALTER TABLE public.media OWNER TO "user";

--
-- Name: mediaversion; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE mediaversion (
    latest integer
);


ALTER TABLE public.mediaversion OWNER TO "user";

--
-- Name: moviesversion; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE moviesversion (
    latest integer
);


ALTER TABLE public.moviesversion OWNER TO "user";

--
-- Name: parsequeue; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE parsequeue (
    id integer NOT NULL,
    added timestamp with time zone DEFAULT now() NOT NULL,
    uri text,
    tries integer DEFAULT 0,
    done boolean DEFAULT false
);


ALTER TABLE public.parsequeue OWNER TO "user";

--
-- Name: parsequeue_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE parsequeue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.parsequeue_id_seq OWNER TO "user";

--
-- Name: parsequeue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE parsequeue_id_seq OWNED BY parsequeue.id;


--
-- Name: queryoffsets; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE queryoffsets (
    posi INTEGER[],
    nega INTEGER[],
    ioffset integer,
    ooffset integer,
    created timestamp with time zone DEFAULT clock_timestamp()
);


ALTER TABLE public.queryoffsets OWNER TO "user";

--
-- Name: randomseen; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE randomseen (
    id integer NOT NULL,
    media INTEGER,
    category integer DEFAULT 0
);


ALTER TABLE public.randomseen OWNER TO "user";

--
-- Name: randomseen_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE randomseen_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.randomseen_id_seq OWNER TO "user";

--
-- Name: randomseen_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE randomseen_id_seq OWNED BY randomseen.id;


--
-- Name: randomversion; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE randomversion (
    latest integer
);


ALTER TABLE public.randomversion OWNER TO "user";

--
-- Name: savecomicpages; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE savecomicpages (
    id integer,
    comic integer,
    which integer,
    image integer
);


ALTER TABLE public.savecomicpages OWNER TO "user";

--
-- Name: sources; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE sources (
    id integer NOT NULL,
    checked timestamp with time zone DEFAULT clock_timestamp()
);


ALTER TABLE public.sources OWNER TO "user";

--
-- Name: sources_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sources_id_seq OWNER TO "user";

--
-- Name: sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE sources_id_seq OWNED BY sources.id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE tags (
    id INTEGER NOT NULL,
    name text
);


ALTER TABLE public.tags OWNER TO "user";

--
-- Name: things; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE things (
    id INTEGER NOT NULL,
    neighbors INTEGER[]
);


ALTER TABLE public.things OWNER TO "user";

--
-- Name: things_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE things_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.things_id_seq OWNER TO "user";

--
-- Name: things_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE things_id_seq OWNED BY things.id;


--
-- Name: uploads; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE uploads (
    uzer integer,
    media INTEGER,
    checked boolean DEFAULT false
);


ALTER TABLE public.uploads OWNER TO "user";

--
-- Name: urisources; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE urisources (
    id integer NOT NULL,
    uri text NOT NULL,
    code integer
);


ALTER TABLE public.urisources OWNER TO "user";

--
-- Name: userversion; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE userversion (
    latest integer
);


ALTER TABLE public.userversion OWNER TO "user";

--
-- Name: uzers; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE uzers (
    id integer NOT NULL,
    ident text,
    rescaleimages boolean DEFAULT true,
    defaulttags boolean DEFAULT false
);


ALTER TABLE public.uzers OWNER TO "user";

--
-- Name: uzer_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE uzer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.uzer_id_seq OWNER TO "user";

--
-- Name: uzer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE uzer_id_seq OWNED BY uzers.id;


--
-- Name: uzertags; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE uzertags (
    id integer NOT NULL,
    tag INTEGER,
    uzer integer,
    nega boolean DEFAULT false
);


ALTER TABLE public.uzertags OWNER TO "user";

--
-- Name: uzertags2_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE uzertags2_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.uzertags2_id_seq OWNER TO "user";

--
-- Name: uzertags2_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE uzertags2_id_seq OWNED BY uzertags.id;


--
-- Name: videos; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE videos (
    id INTEGER NOT NULL,
    width integer,
    height integer,
    fps double precision,
    vcodec text,
    acodec text,
    container text
);


ALTER TABLE public.videos OWNER TO "user";

--
-- Name: visited; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE visited (
    id integer NOT NULL,
    uzer integer,
    medium INTEGER,
    visits integer DEFAULT 0
);


ALTER TABLE public.visited OWNER TO "user";

--
-- Name: visited_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE visited_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.visited_id_seq OWNER TO "user";

--
-- Name: visited_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE visited_id_seq OWNED BY visited.id;


SET search_path = resultcache, pg_catalog;

--
-- Name: q-z8GeQZryx-tM2EYrYYF2bsQFu8; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q-z8GeQZryx-tM2EYrYYF2bsQFu8" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."q-z8GeQZryx-tM2EYrYYF2bsQFu8" OWNER TO "user";

--
-- Name: q2AYSoZWiecyi2hcrIMvyYk4bN44; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q2AYSoZWiecyi2hcrIMvyYk4bN44" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."q2AYSoZWiecyi2hcrIMvyYk4bN44" OWNER TO "user";

--
-- Name: q2tu9Yr_bTmwoSvUFp_Kj4P9Zqz4; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q2tu9Yr_bTmwoSvUFp_Kj4P9Zqz4" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."q2tu9Yr_bTmwoSvUFp_Kj4P9Zqz4" OWNER TO "user";

--
-- Name: q4PGCcCdA1G5R3_mg7B470n7l9CY; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q4PGCcCdA1G5R3_mg7B470n7l9CY" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."q4PGCcCdA1G5R3_mg7B470n7l9CY" OWNER TO "user";

--
-- Name: q79Gdtf4DrdaiBXOGHYgD2nF3jHU; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q79Gdtf4DrdaiBXOGHYgD2nF3jHU" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."q79Gdtf4DrdaiBXOGHYgD2nF3jHU" OWNER TO "user";

--
-- Name: q8mrNXKvZLjgHvTvOCQSKDdWad8A; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q8mrNXKvZLjgHvTvOCQSKDdWad8A" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."q8mrNXKvZLjgHvTvOCQSKDdWad8A" OWNER TO "user";

--
-- Name: qBIHMNcGL1hbwxc9yi3u_JRSjfp4; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qBIHMNcGL1hbwxc9yi3u_JRSjfp4" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qBIHMNcGL1hbwxc9yi3u_JRSjfp4" OWNER TO "user";

--
-- Name: qDc8LBI4UllkApWBYlu0wt_bC1LQ; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qDc8LBI4UllkApWBYlu0wt_bC1LQ" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qDc8LBI4UllkApWBYlu0wt_bC1LQ" OWNER TO "user";

--
-- Name: qECwqVfHpq6jp3RIqaaJY2ZePXdI; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qECwqVfHpq6jp3RIqaaJY2ZePXdI" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qECwqVfHpq6jp3RIqaaJY2ZePXdI" OWNER TO "user";

--
-- Name: qImfoIkXHIwyAodZKw4kK4tyFA1w; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qImfoIkXHIwyAodZKw4kK4tyFA1w" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qImfoIkXHIwyAodZKw4kK4tyFA1w" OWNER TO "user";

--
-- Name: qJ4YjoQrU-xLlODIqlgk7Tw_mh9U; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qJ4YjoQrU-xLlODIqlgk7Tw_mh9U" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qJ4YjoQrU-xLlODIqlgk7Tw_mh9U" OWNER TO "user";

--
-- Name: qJScke_npFNV1IyuqA6B3yy1tf54; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qJScke_npFNV1IyuqA6B3yy1tf54" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qJScke_npFNV1IyuqA6B3yy1tf54" OWNER TO "user";

--
-- Name: qJ_8yPV2cHI_w3cfmjd-Tqw3w7jo; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qJ_8yPV2cHI_w3cfmjd-Tqw3w7jo" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qJ_8yPV2cHI_w3cfmjd-Tqw3w7jo" OWNER TO "user";

--
-- Name: qLjXVNHr-6Vu7pfBLWxUVD7eWRik; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qLjXVNHr-6Vu7pfBLWxUVD7eWRik" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qLjXVNHr-6Vu7pfBLWxUVD7eWRik" OWNER TO "user";

--
-- Name: qMn2vW6eu8zFmZMs4GpMKJ1QxXl0; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qMn2vW6eu8zFmZMs4GpMKJ1QxXl0" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qMn2vW6eu8zFmZMs4GpMKJ1QxXl0" OWNER TO "user";

--
-- Name: qNyP-Y09e8L_hrpCsOGra9hf33MY; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qNyP-Y09e8L_hrpCsOGra9hf33MY" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qNyP-Y09e8L_hrpCsOGra9hf33MY" OWNER TO "user";

--
-- Name: qO5c54xbyLU96WV-tuhzW8WtrMpk; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qO5c54xbyLU96WV-tuhzW8WtrMpk" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qO5c54xbyLU96WV-tuhzW8WtrMpk" OWNER TO "user";

--
-- Name: qOBOgBg1tdm_wEKZOhnCEy8pOBnY; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qOBOgBg1tdm_wEKZOhnCEy8pOBnY" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qOBOgBg1tdm_wEKZOhnCEy8pOBnY" OWNER TO "user";

--
-- Name: qOyxm4RUyqHLwB2o2EERmkVddWOA; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qOyxm4RUyqHLwB2o2EERmkVddWOA" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qOyxm4RUyqHLwB2o2EERmkVddWOA" OWNER TO "user";

--
-- Name: qOzmy0CzzXUOd821CtcBxXeGjD_g; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qOzmy0CzzXUOd821CtcBxXeGjD_g" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qOzmy0CzzXUOd821CtcBxXeGjD_g" OWNER TO "user";

--
-- Name: qRNvBW_WPZnzLIN8kc94AjkYjQ_o; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qRNvBW_WPZnzLIN8kc94AjkYjQ_o" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qRNvBW_WPZnzLIN8kc94AjkYjQ_o" OWNER TO "user";

--
-- Name: qS95_81u_yUfuCwgIWuqiyTQrUSw; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qS95_81u_yUfuCwgIWuqiyTQrUSw" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qS95_81u_yUfuCwgIWuqiyTQrUSw" OWNER TO "user";

--
-- Name: qWWT2HVTBvKmiEC9IOxLC9qOmTUk; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qWWT2HVTBvKmiEC9IOxLC9qOmTUk" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qWWT2HVTBvKmiEC9IOxLC9qOmTUk" OWNER TO "user";

--
-- Name: qXA5dnqFqedLxJcUcV1O7jNtUWEo; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qXA5dnqFqedLxJcUcV1O7jNtUWEo" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qXA5dnqFqedLxJcUcV1O7jNtUWEo" OWNER TO "user";

--
-- Name: qXjXFlRs6aVlZOvg3JkfbQVGoBA8; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qXjXFlRs6aVlZOvg3JkfbQVGoBA8" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qXjXFlRs6aVlZOvg3JkfbQVGoBA8" OWNER TO "user";

--
-- Name: q_SitDDhgmMWnXQLgAYfORJxEako; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q_SitDDhgmMWnXQLgAYfORJxEako" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."q_SitDDhgmMWnXQLgAYfORJxEako" OWNER TO "user";

--
-- Name: qiJTqYrhoApmGp5F7_b2GWT_IWQY; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qiJTqYrhoApmGp5F7_b2GWT_IWQY" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qiJTqYrhoApmGp5F7_b2GWT_IWQY" OWNER TO "user";

--
-- Name: qjnDdR9eOeon3iJagRuC-AEj_MHQ; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qjnDdR9eOeon3iJagRuC-AEj_MHQ" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qjnDdR9eOeon3iJagRuC-AEj_MHQ" OWNER TO "user";

--
-- Name: qky6gfav1QCvK-uob2JViml6lq0U; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qky6gfav1QCvK-uob2JViml6lq0U" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qky6gfav1QCvK-uob2JViml6lq0U" OWNER TO "user";

--
-- Name: qn9tadg88rgQkpjdEA-tPmBCBiUQ; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qn9tadg88rgQkpjdEA-tPmBCBiUQ" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qn9tadg88rgQkpjdEA-tPmBCBiUQ" OWNER TO "user";

--
-- Name: qoG8bFGXsZ5N0vCY2GFcKgzfpdgQ; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qoG8bFGXsZ5N0vCY2GFcKgzfpdgQ" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qoG8bFGXsZ5N0vCY2GFcKgzfpdgQ" OWNER TO "user";

--
-- Name: qoRERGH1Waygq-wgtbvB6LukZ19Q; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qoRERGH1Waygq-wgtbvB6LukZ19Q" (
    id INTEGER,
    name text
);


ALTER TABLE resultcache."qoRERGH1Waygq-wgtbvB6LukZ19Q" OWNER TO "user";

--
-- Name: qsDHHa_fvhUKA11Vnn0wTOWnbozo; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qsDHHa_fvhUKA11Vnn0wTOWnbozo" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qsDHHa_fvhUKA11Vnn0wTOWnbozo" OWNER TO "user";

--
-- Name: queries; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE queries (
    id integer NOT NULL,
    digest text,
    created timestamp with time zone DEFAULT clock_timestamp()
);


ALTER TABLE resultcache.queries OWNER TO "user";

--
-- Name: queries_id_seq; Type: SEQUENCE; Schema: resultcache; Owner: user
--

CREATE SEQUENCE queries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE resultcache.queries_id_seq OWNER TO "user";

--
-- Name: queries_id_seq; Type: SEQUENCE OWNED BY; Schema: resultcache; Owner: user
--

ALTER SEQUENCE queries_id_seq OWNED BY queries.id;


--
-- Name: qvzHILWpLpuwn96H9Cc_l0qaOaBU; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qvzHILWpLpuwn96H9Cc_l0qaOaBU" (
    id INTEGER,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qvzHILWpLpuwn96H9Cc_l0qaOaBU" OWNER TO "user";

SET search_path = public, pg_catalog;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY blacklist ALTER COLUMN id SET DEFAULT nextval('blacklist_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY comicpage ALTER COLUMN id SET DEFAULT nextval('comicpage_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY connections ALTER COLUMN id SET DEFAULT nextval('connections_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY dupes ALTER COLUMN id SET DEFAULT nextval('dupes_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY parsequeue ALTER COLUMN id SET DEFAULT nextval('parsequeue_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY randomseen ALTER COLUMN id SET DEFAULT nextval('randomseen_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY sources ALTER COLUMN id SET DEFAULT nextval('sources_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY things ALTER COLUMN id SET DEFAULT nextval('things_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY uzers ALTER COLUMN id SET DEFAULT nextval('uzer_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY uzertags ALTER COLUMN id SET DEFAULT nextval('uzertags2_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY visited ALTER COLUMN id SET DEFAULT nextval('visited_id_seq'::regclass);


SET search_path = resultcache, pg_catalog;

--
-- Name: id; Type: DEFAULT; Schema: resultcache; Owner: user
--

ALTER TABLE ONLY queries ALTER COLUMN id SET DEFAULT nextval('queries_id_seq'::regclass);


SET search_path = public, pg_catalog;

--
-- Name: badfiles_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY badfiles
    ADD CONSTRAINT badfiles_pkey PRIMARY KEY (path);


--
-- Name: blacklist_hash_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY blacklist
    ADD CONSTRAINT blacklist_hash_key UNIQUE (hash);


--
-- Name: blacklist_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY blacklist
    ADD CONSTRAINT blacklist_pkey PRIMARY KEY (id);


--
-- Name: comic_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY comics
    ADD CONSTRAINT comic_pkey PRIMARY KEY (id);


--
-- Name: comic_title_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY comics
    ADD CONSTRAINT comic_title_key UNIQUE (title);


--
-- Name: comicpage_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY comicpage
    ADD CONSTRAINT comicpage_pkey PRIMARY KEY (id);


--
-- Name: connections_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY connections
    ADD CONSTRAINT connections_pkey PRIMARY KEY (id);


--
-- Name: connections_source_dest_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY connections
    ADD CONSTRAINT connections_source_dest_key UNIQUE (source, dest);


--
-- Name: desktops_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY desktops
    ADD CONSTRAINT desktops_pkey PRIMARY KEY (id);


--
-- Name: dupes_hash_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY dupes
    ADD CONSTRAINT dupes_hash_key UNIQUE (hash);


--
-- Name: dupes_medium_hash_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY dupes
    ADD CONSTRAINT dupes_medium_hash_key UNIQUE (medium, hash);


--
-- Name: dupes_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY dupes
    ADD CONSTRAINT dupes_pkey PRIMARY KEY (id);


--
-- Name: filesources_path_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY filesources
    ADD CONSTRAINT filesources_path_key UNIQUE (path);


--
-- Name: filesources_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY filesources
    ADD CONSTRAINT filesources_pkey PRIMARY KEY (id);


--
-- Name: images_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY images
    ADD CONSTRAINT images_pkey PRIMARY KEY (id);


--
-- Name: media_hash_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY media
    ADD CONSTRAINT media_hash_key UNIQUE (hash);


--
-- Name: media_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY media
    ADD CONSTRAINT media_pkey PRIMARY KEY (id);


--
-- Name: parsequeue_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY parsequeue
    ADD CONSTRAINT parsequeue_pkey PRIMARY KEY (id);


--
-- Name: parsequeue_uri_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY parsequeue
    ADD CONSTRAINT parsequeue_uri_key UNIQUE (uri);


--
-- Name: queryoffsets_created_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY queryoffsets
    ADD CONSTRAINT queryoffsets_created_key UNIQUE (created);


--
-- Name: queryoffsets_posi_nega_ioffset_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY queryoffsets
    ADD CONSTRAINT queryoffsets_posi_nega_ioffset_key UNIQUE (posi, nega, ioffset);


--
-- Name: queryoffsets_posi_nega_ooffset_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY queryoffsets
    ADD CONSTRAINT queryoffsets_posi_nega_ooffset_key UNIQUE (posi, nega, ooffset);


--
-- Name: randomseen_media_category_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY randomseen
    ADD CONSTRAINT randomseen_media_category_key UNIQUE (media, category);


--
-- Name: randomseen_media_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY randomseen
    ADD CONSTRAINT randomseen_media_key UNIQUE (media);


--
-- Name: randomseen_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY randomseen
    ADD CONSTRAINT randomseen_pkey PRIMARY KEY (id);


--
-- Name: sources_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY sources
    ADD CONSTRAINT sources_pkey PRIMARY KEY (id);


--
-- Name: tags_name_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_name_key UNIQUE (name);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: things_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY things
    ADD CONSTRAINT things_pkey PRIMARY KEY (id);


--
-- Name: urisources_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY urisources
    ADD CONSTRAINT urisources_pkey PRIMARY KEY (id);


--
-- Name: urisources_uri_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY urisources
    ADD CONSTRAINT urisources_uri_key UNIQUE (uri);


--
-- Name: uzer_ident_key; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY uzers
    ADD CONSTRAINT uzer_ident_key UNIQUE (ident);


--
-- Name: uzer_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY uzers
    ADD CONSTRAINT uzer_pkey PRIMARY KEY (id);


--
-- Name: uzertags2_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY uzertags
    ADD CONSTRAINT uzertags2_pkey PRIMARY KEY (id);


--
-- Name: videos_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (id);


--
-- Name: visited_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY visited
    ADD CONSTRAINT visited_pkey PRIMARY KEY (id);


SET search_path = resultcache, pg_catalog;

--
-- Name: queries_digest_key; Type: CONSTRAINT; Schema: resultcache; Owner: user; Tablespace: 
--

ALTER TABLE ONLY queries
    ADD CONSTRAINT queries_digest_key UNIQUE (digest);


--
-- Name: queries_pkey; Type: CONSTRAINT; Schema: resultcache; Owner: user; Tablespace: 
--

ALTER TABLE ONLY queries
    ADD CONSTRAINT queries_pkey PRIMARY KEY (id);


SET search_path = public, pg_catalog;

--
-- Name: bypath; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX bypath ON filesources USING btree (path);


--
-- Name: bytype; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX bytype ON media USING btree (type);


--
-- Name: byuri; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX byuri ON urisources USING btree (uri);


--
-- Name: md5derp; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX md5derp ON media USING btree (md5);


--
-- Name: mostrecent; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE UNIQUE INDEX mostrecent ON media USING btree (added);


--
-- Name: nodupesuploads; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE UNIQUE INDEX nodupesuploads ON uploads USING btree (uzer, media);


--
-- Name: nodupeuzertags; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE UNIQUE INDEX nodupeuzertags ON uzertags USING btree (tag, uzer);


--
-- Name: oldest; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX oldest ON media USING btree (created);


--
-- Name: posinega; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX posinega ON queryoffsets USING btree (posi, nega);


--
-- Name: sourcessearch; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX sourcessearch ON media USING gin (sources);


--
-- Name: tagsearch; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE INDEX tagsearch ON things USING gin (neighbors);


--
-- Name: unique_pages; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE UNIQUE INDEX unique_pages ON comicpage USING btree (comic, which);


--
-- Name: visitorunique; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE UNIQUE INDEX visitorunique ON visited USING btree (uzer, medium);


--
-- Name: whenchecked; Type: INDEX; Schema: public; Owner: user; Tablespace: 
--

CREATE UNIQUE INDEX whenchecked ON sources USING btree (checked);


--
-- Name: emptythings; Type: TRIGGER; Schema: public; Owner: user
--

CREATE TRIGGER emptythings AFTER DELETE ON things FOR EACH ROW EXECUTE PROCEDURE clearneighbors();


--
-- Name: expiretrigger; Type: TRIGGER; Schema: public; Owner: user
--

CREATE TRIGGER expiretrigger AFTER INSERT OR DELETE OR UPDATE ON things FOR EACH STATEMENT EXECUTE PROCEDURE resultcache.expirequeriestrigger();


--
-- Name: comicpage_comic_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY comicpage
    ADD CONSTRAINT comicpage_comic_fkey FOREIGN KEY (comic) REFERENCES comics(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comicpage_media_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY comicpage
    ADD CONSTRAINT comicpage_media_fkey FOREIGN KEY (medium) REFERENCES media(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comics_source_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY comics
    ADD CONSTRAINT comics_source_fkey FOREIGN KEY (source) REFERENCES sources(id);


--
-- Name: connections_dest_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY connections
    ADD CONSTRAINT connections_dest_fkey FOREIGN KEY (dest) REFERENCES things(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: connections_source_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY connections
    ADD CONSTRAINT connections_source_fkey FOREIGN KEY (dest) REFERENCES things(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: desktops_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY desktops
    ADD CONSTRAINT desktops_id_fkey FOREIGN KEY (id) REFERENCES images(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: dupes_medium_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY dupes
    ADD CONSTRAINT dupes_medium_fkey FOREIGN KEY (medium) REFERENCES media(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: filesources_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY filesources
    ADD CONSTRAINT filesources_id_fkey FOREIGN KEY (id) REFERENCES sources(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: images_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY images
    ADD CONSTRAINT images_id_fkey FOREIGN KEY (id) REFERENCES media(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY media
    ADD CONSTRAINT media_id_fkey FOREIGN KEY (id) REFERENCES things(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: randomseen_media_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY randomseen
    ADD CONSTRAINT randomseen_media_fkey FOREIGN KEY (media) REFERENCES things(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tags_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_id_fkey FOREIGN KEY (id) REFERENCES things(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: uploads_media_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY uploads
    ADD CONSTRAINT uploads_media_fkey FOREIGN KEY (media) REFERENCES media(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: uploads_uzer_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY uploads
    ADD CONSTRAINT uploads_uzer_fkey FOREIGN KEY (uzer) REFERENCES uzers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: urisources_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY urisources
    ADD CONSTRAINT urisources_id_fkey FOREIGN KEY (id) REFERENCES sources(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: uzertags2_tag_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY uzertags
    ADD CONSTRAINT uzertags2_tag_fkey FOREIGN KEY (tag) REFERENCES tags(id);


--
-- Name: uzertags2_uzer_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY uzertags
    ADD CONSTRAINT uzertags2_uzer_fkey FOREIGN KEY (uzer) REFERENCES uzers(id);


--
-- Name: videos_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY videos
    ADD CONSTRAINT videos_id_fkey FOREIGN KEY (id) REFERENCES things(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: visited_medium_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY visited
    ADD CONSTRAINT visited_medium_fkey FOREIGN KEY (medium) REFERENCES media(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: visited_uzer_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY visited
    ADD CONSTRAINT visited_uzer_fkey FOREIGN KEY (uzer) REFERENCES uzers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: user
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM "user";
GRANT ALL ON SCHEMA public TO "user";
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

