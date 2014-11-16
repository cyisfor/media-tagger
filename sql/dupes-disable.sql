update media set phash = encode('\x00000000000004'::bytea || substring(uuid_send(phash) from 8),'hex')::uuid where type = 'image/x-xcf';
