SELECT a,b,hash FROM (select a.id as a, b.id as b,a.pHash as hash FROM media a, media b
WHERE a.id != b.id AND NOT a.pHashFail AND a.pHash = b.pHash) AS hashey
left outer join nadupes ON nadupes.bro = a and nadupes.sis = b
left outer join nadupes nd2 on nd2.sis = a and nd2.bro = b
WHERE nadupes.id IS NULL AND nd2.id IS NULL
