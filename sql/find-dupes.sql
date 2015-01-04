SELECT a.id as a,b.id as b,a.pHash as hash FROM 
media a inner join media b on a.phash = b.phash
