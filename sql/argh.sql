EXPLAIN ANALYZE WITH wanted(tags) AS (SELECT (
        SELECT array_agg(tags.id) as wanteds 
            FROM tags INNER JOIN things ON tags.id = things.id WHERE things.neighbors @> ARRAY[unnest.unnest]
        ) || unnest.unnest AS tags
    FROM unnest(ARRAY[219772, 215845]::INTEGER[]) AS unnest)
SELECT 
(select media.id from media where media.id = result.id),
(select array_agg(tags.name) from tags inner join unnest(result.neighbors) AS unnest ON tags.id = unnest.unnest)
FROM (SELECT media.id,things.neighbors, every(things.neighbors && wanted.tags) FROM media INNER JOIN things ON things.id = media.id, wanted group by media.id,things.neighbors) AS result WHERE result.every AND NOT result.neighbors && ARRAY[217367, 216419]::INTEGER[];

Subquery Scan on result  (cost=2237889.32..6578010925.32 rows=8907500 width=141) (actual time=2188.987..3028.893 rows=861 loops=1)
  CTE wanted
    ->  Function Scan on unnest  (cost=0.00..326013.51 rows=100 width=8) (actual time=339.310..501.420 rows=2 loops=1)
          SubPlan 1
            ->  Aggregate  (cost=3260.11..3260.12 rows=1 width=8) (actual time=250.663..250.664 rows=1 loops=2)
                  ->  Hash Join  (cost=1677.37..3259.13 rows=393 width=8) (actual time=250.119..250.119 rows=0 loops=2)
                        Hash Cond: (public.tags.id = public.things.id)
                        ->  Seq Scan on tags  (cost=0.00..1283.33 rows=78533 width=8) (actual time=0.014..75.088 rows=77587 loops=2)
                        ->  Hash  (cost=1666.92..1666.92 rows=836 width=8) (actual time=46.991..46.991 rows=12721 loops=2)
                              Buckets: 1024  Batches: 1  Memory Usage: 84kB
                              ->  Bitmap Heap Scan on things  (cost=22.48..1666.92 rows=836 width=8) (actual time=2.897..31.442 rows=12721 loops=2)
                                    Recheck Cond: (neighbors @> ARRAY[unnest.unnest])
                                    ->  Bitmap Index Scan on tagsearch  (cost=0.00..22.27 rows=836 width=0) (actual time=2.647..2.647 rows=12721 loops=2)
                                          Index Cond: (neighbors @> ARRAY[unnest.unnest])
  ->  GroupAggregate  (cost=1911875.81..2156832.06 rows=8907500 width=173) (actual time=2188.483..2757.345 rows=861 loops=1)
        Filter: every((public.things.neighbors && wanted.tags))
        Rows Removed by Filter: 87160
        ->  Sort  (cost=1911875.81..1934144.56 rows=8907500 width=173) (actual time=2170.364..2359.773 rows=176042 loops=1)
              Sort Key: public.media.id, public.things.neighbors
              Sort Method: quicksort  Memory: 55152kB
              ->  Nested Loop  (cost=4276.23..122515.35 rows=8907500 width=173) (actual time=587.928..1764.202 rows=176042 loops=1)
                    ->  CTE Scan on wanted  (cost=0.00..2.00 rows=100 width=32) (actual time=339.323..501.446 rows=2 loops=1)
                    ->  Materialize  (cost=4276.23..11392.28 rows=89075 width=141) (actual time=124.299..469.096 rows=88021 loops=2)
                          ->  Hash Join  (cost=4276.23..10946.91 rows=89075 width=141) (actual time=248.589..651.358 rows=88021 loops=1)
                                Hash Cond: (public.things.id = public.media.id)
                                ->  Seq Scan on things  (cost=0.00..4330.81 rows=165613 width=141) (actual time=12.802..183.116 rows=88021 loops=1)
                                      Filter: (NOT (neighbors && '{217367,216419}'::INTEGER[]))
                                      Rows Removed by Filter: 79084
                                ->  Hash  (cost=3152.77..3152.77 rows=89877 width=8) (actual time=235.641..235.641 rows=89518 loops=1)
                                      Buckets: 16384  Batches: 1  Memory Usage: 3497kB
                                      ->  Seq Scan on media  (cost=0.00..3152.77 rows=89877 width=8) (actual time=0.022..120.713 rows=89518 loops=1)
  SubPlan 3
    ->  Index Only Scan using media_pkey on media  (cost=0.00..8.37 rows=1 width=8) (actual time=0.016..0.018 rows=1 loops=861)
          Index Cond: (id = result.id)
          Heap Fetches: 861
  SubPlan 4
    ->  Aggregate  (cost=729.82..729.83 rows=1 width=12) (actual time=0.287..0.288 rows=1 loops=861)
          ->  Nested Loop  (cost=0.00..729.56 rows=100 width=12) (actual time=0.018..0.252 rows=24 loops=861)
                ->  Function Scan on unnest  (cost=0.00..1.00 rows=100 width=8) (actual time=0.009..0.031 rows=24 loops=861)
                ->  Index Scan using tags_pkey on tags  (cost=0.00..7.28 rows=1 width=20) (actual time=0.004..0.005 rows=1 loops=20969)
                      Index Cond: (id = unnest.unnest)
Total runtime: 3088.804 ms
