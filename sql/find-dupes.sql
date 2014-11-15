with hashes as (select * from (
    select id,
        derphash,
        ('x' || derphash)::bit(64)::int8 as phash, 
        flags
    from (
        select id,
        encode(substring(uuid_send(phash) from 10),'hex') as derphash,
        ('x' || encode(substring(uuid_send(pHash) from 1 for 8),'hex'))::bit(64)::int8 as flags 
            from media
            where phash != '00000000-0000-0000-0000-000000000002'
            and phash != '00000000-0000-0000-0000-000000000001'
            and phash != '00000000-0000-0000-0000-000000000000'
        )
        as derp1
    ) 
    as derp2 where phash != 0 and flags = 0)
    select a.id as a, b.id as b, a.derphash as hash from hashes a, hashes b where a.id > b.id and a.phash = b.phash order by a.id desc;

