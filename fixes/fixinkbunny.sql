CREATE OR REPLACE FUNCTION fixinkbunny() RETURNS void AS $$
DECLARE
_authortag int;
BEGIN
	SELECT findTag('artist:a6p',CATGEGORYR) INTO _authortag;
	SELECT connectOne(_authortag,
	
SELECT connectOne((select id from media where sources @> ARRAY[urisources.id]),(select findTag(substring(uri from 'metapix.net/files/full/[0-9]+/[0-9]+_([^_]+)')))),
uri FROM urisources WHERE
substring(uri from 'metapix.net/files/full/[0-9]+/[0-9]+_([^_]+)') IS NOT NULL
;
	
