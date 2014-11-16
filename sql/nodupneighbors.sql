delete from things where id in (select things.id from things left outer join tags on tags.id = things.id left outer join media on media.id = things.id left outer join videos on videos.id = things.id where tags.id IS NULL and media.id IS NULL and videos.id IS NULL);

update things set neighbors = q.better FROM (
        select id,
        array(
            select unnest from (
                select distinct unnest(neighbors)) as bb where EXISTS(
                select id from things where bb.unnest = id)) as better,
        neighbors 
        from things order by id) as q 
    where array_length(better,1) != array_length(q.neighbors,1) AND things.id = q.id;

