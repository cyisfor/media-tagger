create or replace function shiftComicPageUp(_comic integer, _spot integer, _target integer)
  returns void as $$
declare
  r record;
  _targetid integer;
begin
  SELECT id INTO _targetid FROM comicPage WHERE comic = _comic AND which = _target;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'The target page was not found %', _target;
  END IF;

  UPDATE comicPage SET which = NULL WHERE id = _targetid;
  
  for r in 
    select id
      from comicPage 
      where comic = _comic and which > _target and which <= _spot
      order by which asc
  loop
    update comicPage
      set which = which - 1
      where id = r.id;
  end loop;

  update comicPage  set which = _spot where id = _targetid;
end;
$$ language plpgsql;


create or replace function shiftComicPage(_comic integer, _spot integer, _target integer DEFAULT NULL)
  returns void as $$
declare
  r record;
  _targetid integer;
begin
  IF _target IS NOT NULL THEN
      SELECT id INTO _targetid FROM comicPage WHERE comic = _comic AND which = _target;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'The target page was not found %', _target;
      END IF;
  END IF;
  
  for r in 
    select id
      from comicPage 
      where comic = _comic and which >= _spot
      order by which desc 
  loop
    update comicPage
      set which = which + 1
      where id = r.id;
  end loop;
  
  IF _target IS NOT NULL THEN
    update comicPage
      set which = _spot
      where id = _targetid;
  END IF;
end;
$$ language plpgsql;
