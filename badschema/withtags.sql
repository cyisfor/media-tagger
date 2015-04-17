EXPLAIN ANALYZE with things(blue) AS (
    %(criteria)s
), imagethings(blue) AS (
    SELECT blue FROM things INNER JOIN images ON images.id = things.blue
), tagthings(blue) AS (
    SELECT blue FROM things INNER JOIN tags ON tags.id = things.blue
), imagetagthings(blue) AS (
    SELECT blue FROM connections WHERE red IN (SELECT blue FROM tagthings)
), imageimages(blue) AS (
    SELECT blue FROM imagetagthings INNER JOIN images ON images.id = imagetagthings.blue
    UNION
    SELECT  blue from imagethings
) SELECT 
    (SELECT array_agg(id) FROM (SELECT id FROM images inner join imageimages ON images.id = imageimages.blue LIMIT 5) AS derp),
    (SELECT array_agg(name) FROM (SELECT name FROM tags WHERE tags.id IN (select connections.blue FROM connections INNER JOIN imageimages ON imageimages.blue = connections.red) LIMIT 5) AS derp);
