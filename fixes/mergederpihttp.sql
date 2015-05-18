select COUNT(a) FROM (select mergeSourceURI(id, 'https://' || substring(uri from 8)) from urisources where uri LIKE 'http://derpicdn.net%' order by id desc limit 1000) AS a;
