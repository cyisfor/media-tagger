select sub.name,first(tags.name),first(tags.id),first(things.id) from things,tags,tags as sub where tags.name = substring(sub.name from '(.*):') AND sub.name LIKE '%:%' AND neighbors @> ARRAY[tags.id] AND NOT tags.id = ANY(array(select id from tags where name = ANY(ARRAY['american dragon','amnesia','avatar','bannertail','c','cad','d','dust','duplicate','edward','furaffinity','for','&gt;','mlp','punisher','csi','fallout','final fantasy 7','generation','','my little pony','planescape','re','skippy','spirit','star trek','the elder scrolls iv','the elder scrolls v','>','werewolf']))) GROUP BY sub.name;
delete from things using tags where tags.name IN (select distinct substring(sub.name from '(.*):') from tags as sub where sub.name LIKE '%:%') and things.id = tags.id and not tags.id = any(array(select id from tags where name = ANY(ARRAY['american dragon','amnesia','avatar','bannertail','c','cad','d','dust','duplicate','edward','furaffinity','for','&gt;','mlp','punisher','csi','fallout','final fantasy 7','generation','','my little pony','planescape','re','skippy','spirit','star trek','the elder scrolls iv','the elder scrolls v','>','werewolf'])));

