delete from media where id in (select media.id from media left outer join tags on tags.id = media.id left outer join videos on videos.id = media.id where tags.id IS NULL and media.id IS NULL and videos.id IS NULL);

update media set sources = q.better FROM (
        select id,
        array(
            select unnest from (
                select distinct unnest(sources)) as bb where EXISTS(
                select id from media where bb.unnest = id)) as better,
        sources 
        from media order by id) as q 
    where array_length(better,1) != array_length(q.sources,1) AND media.id = q.id;

