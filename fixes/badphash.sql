CREATE FUNCTION fuckyoupostgres() RETURNS void AS $$
DECLARE
_derp RECORD;
BEGIN
  FOR _derp IN
       SELECT id,
       phash as phash,
       derp as derp
       FROM (
       select id,
       	      phash,
	      ('x' || substring(encode(uuid_send(derphash),'hex') from 17))::bit(64)::int8 as derp
	      from media
	      where phash & x'ff' = 0 and derphash IS NOT NULL) as feep
	where derp != 0 AND (feep.derp & x'00ffffffffffffff'::int8) << 8 = phash LOOP
	raise NOTICE 'uhhh %', to_hex(x'87d1734939357200'::int8 >> 8);	
	raise NOTICE 'uhhh %', to_hex(x'0087d17349393572'::int8 << x'100'::int);
	raise NOTICE 'herp % %',_derp.id,to_hex(_derp.derp & x'00ffffffffffffff'::int8);
	RAISE NOTICE 'derp % %',to_hex(_derp.phash),to_hex((_derp.derp & x'00ffffffffffffff'::int8) << 8);
  END LOOP;
 END;
$$ LANGUAGE 'plpgsql';

-- SELECT fuckyoupostgres();

DROP FUNCTION fuckyoupostgres();

-- select to_hex(id),to_hex(phash),to_hex(derp) FROM(
--        select id,
--        	      phash,
-- 	      ('x' || substring(encode(uuid_send(derphash),'hex') from 17))::bit(64)::int8 as derp
-- 	      from media
-- 	      where phash & x'ff'::int = 0 and derphash IS NOT NULL) as feep
-- 	where derp != 0 AND (derp & x'00ffffffffffffff'::int8) << 8 = phash;

UPDATE media SET phash = ('x' || substring(encode(uuid_send(derphash),'hex') from 17))::bit(64)::int8 WHERE derphash IS NOT NULL AND phash & x'ff'::int = 0 AND ('x' || substring(encode(uuid_send(derphash),'hex') from 17))::bit(64)::int8 != 0 AND phash = (('x' || substring(encode(uuid_send(derphash),'hex') from 17))::bit(64)::int8 & x'00ffffffffffffff'::int8) << 8 ;
