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
-- Name: connectmanytoone(bigint[], bigint); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connectmanytoone(a bigint[], b bigint) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = ANY(a);
END;
$$;


ALTER FUNCTION public.connectmanytoone(a bigint[], b bigint) OWNER TO "user";

--
-- Name: connectone(bigint, bigint); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connectone(a bigint, b bigint) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT b) where things.id = a;
END;
$$;


ALTER FUNCTION public.connectone(a bigint, b bigint) OWNER TO "user";

--
-- Name: connectonetomany(bigint, bigint[]); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION connectonetomany(a bigint, b bigint[]) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    update things set neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(b)) where things.id = a;
END;
$$;


ALTER FUNCTION public.connectonetomany(a bigint, b bigint[]) OWNER TO "user";

--
-- Name: disconnect(bigint, bigint); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION disconnect(a bigint, b bigint) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE things SET neighbors = (SELECT array_agg(neighb) FROM (SELECT neighb FROM unnest(neighbors) AS neighb EXCEPT SELECT b) AS derp) WHERE id = a and neighbors @> ARRAY[b];
END;
$$;


ALTER FUNCTION public.disconnect(a bigint, b bigint) OWNER TO "user";

--
-- Name: findtag(text); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION findtag(_name text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE 
_id bigint;
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
-- Name: listmedia(bigint[], bigint[], integer, integer); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION listmedia(_posi bigint[], _nega bigint[], _offset integer, _limit integer) RETURNS SETOF bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
_ioffset int;
_ooffset int;
_maxoffset int;
_oldbottom int;
_page int DEFAULT 0;
_base RECORD;
_derp bigint[];
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


ALTER FUNCTION public.listmedia(_posi bigint[], _nega bigint[], _offset integer, _limit integer) OWNER TO "user";

--
-- Name: mergeadded(bigint, bigint); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION mergeadded(_a bigint, _b bigint) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
_aadd timestamptz;
_badd timestamptz;
BEGIN
    _aadd := added FROM media WHERE id = _a;
    _badd := added FROM media WHERE id = _b;
    UPDATE media SET added = NULL WHERE id = _b;
    UPDATE media SET added = GREATEST(_aadd,_badd) WHERE id = _a;
END
$$;


ALTER FUNCTION public.mergeadded(_a bigint, _b bigint) OWNER TO "user";

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
-- Name: setcomicpage(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: user
--

CREATE FUNCTION setcomicpage(_image integer, _comic integer, _which integer) RETURNS void
    LANGUAGE plpgsql
    AS $$

BEGIN                                                  
     LOOP                                               
         -- first try to update the key 
         UPDATE comicPage set image = _image where comic = _comic and which = _which;
         IF found THEN                                  
             RETURN;                                    
         END IF;                                        
         -- not there, so try to insert the key         
         -- if someone else inserts the same key concurrently
         -- we could get a unique-key failure           
         BEGIN                                          
             INSERT INTO comicPage(image,comic,which) VALUES (_image,_comic,_which);
             RETURN;                                    
         EXCEPTION WHEN unique_violation THEN           
             -- Do nothing, and loop to try the UPDATE again.
         END;                                           
     END LOOP;                                          
END;
$$;


ALTER FUNCTION public.setcomicpage(_image integer, _comic integer, _which integer) OWNER TO "user";

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
    image integer
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
-- Name: desktops; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE desktops (
    id bigint NOT NULL,
    selected timestamp with time zone DEFAULT clock_timestamp() NOT NULL
);


ALTER TABLE public.desktops OWNER TO "user";

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
    id bigint NOT NULL,
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
    id bigint NOT NULL,
    name text,
    hash character(28),
    created timestamp with time zone,
    added timestamp with time zone DEFAULT clock_timestamp(),
    size integer,
    type text,
    md5 character(32),
    thumbnailed timestamp with time zone,
    sources integer[],
    modified timestamp with time zone DEFAULT clock_timestamp()
);


ALTER TABLE public.media OWNER TO "user";

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
    posi bigint[],
    nega bigint[],
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
    media bigint,
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
    id bigint NOT NULL,
    name text
);


ALTER TABLE public.tags OWNER TO "user";

--
-- Name: things; Type: TABLE; Schema: public; Owner: user; Tablespace: 
--

CREATE TABLE things (
    id bigint NOT NULL,
    neighbors bigint[]
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
    media bigint,
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
    tag bigint,
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
    id bigint NOT NULL,
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
    medium bigint,
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
-- Name: q9cVc6wkk4oPXV8922K7Q2hWmZzk; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "q9cVc6wkk4oPXV8922K7Q2hWmZzk" (
    id bigint,
    name text
);


ALTER TABLE resultcache."q9cVc6wkk4oPXV8922K7Q2hWmZzk" OWNER TO "user";

--
-- Name: qIX-YiYuFfZZLbXLlHJ1q1gpFZGw; Type: TABLE; Schema: resultcache; Owner: user; Tablespace: 
--

CREATE TABLE "qIX-YiYuFfZZLbXLlHJ1q1gpFZGw" (
    id bigint,
    name text,
    type text,
    "array" text[]
);


ALTER TABLE resultcache."qIX-YiYuFfZZLbXLlHJ1q1gpFZGw" OWNER TO "user";

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
-- Name: desktops_pkey; Type: CONSTRAINT; Schema: public; Owner: user; Tablespace: 
--

ALTER TABLE ONLY desktops
    ADD CONSTRAINT desktops_pkey PRIMARY KEY (id);


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
-- Name: comicpage_image_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY comicpage
    ADD CONSTRAINT comicpage_image_fkey FOREIGN KEY (image) REFERENCES images(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comics_source_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY comics
    ADD CONSTRAINT comics_source_fkey FOREIGN KEY (source) REFERENCES sources(id);


--
-- Name: desktops_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY desktops
    ADD CONSTRAINT desktops_id_fkey FOREIGN KEY (id) REFERENCES images(id) ON UPDATE CASCADE ON DELETE CASCADE;


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
    ADD CONSTRAINT randomseen_media_fkey FOREIGN KEY (media) REFERENCES things(id);


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

