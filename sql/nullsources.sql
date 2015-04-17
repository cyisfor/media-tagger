--drop extension intarray;
update media set sources = boo.sources from (
       select id, array_agg(source) sources FROM (
              select id,unnest(sources) source from media where EXISTS(
                     select * from unnest(sources) source where source IS NULL)) boo
              where source IS NOT NULL group by id) boo
      where media.id = boo.id;

--create extension intarray;
