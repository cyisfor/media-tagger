nonconflicted {
UPDATE urisources as upper SET uri = {replacement} where uri LIKE $1  AND NOT EXISTS(select id from urisources where uri = {replacement})
}

httpReplacement {
this is just an example, use parameters!
'https://' || substring(upper.uri from 8)
}

prefixReplacement {
$2 || substring(upper.uri from $3)
}

createMergeit {
create temporary table mergeit as
       select id,(select id from urisources where uri = 'https://' || substring(upper.uri from 8)) as dest,uri from urisources upper where uri LIKE $1
}

-- 'http://derpiboo%';

resolveConflicts {
update media set sources = array(select unnest(sources) except select mergeit.id union select mergeit.dest) from mergeit where  media.sources @> ARRAY[mergeit.id]
}

deleteLeftovers {
delete from urisources where id IN (select id from mergeit)
}
