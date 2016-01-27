from dbconn import prepare,exec
from sqldelite import Bind
from strutils import repeat

exec("""CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY,
limit INTEGER,
offset INTEGER)""")

exec("""CREATE TABLE IF NOT EXISTS results_tags (id INTEGER PRIMARY KEY,
  result NOT NULL REFERENCES results(id) ON DELETE CASCADE ON UPDATE CASCADE,
  tag INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE,
UNIQUE(result,tag))""")

exec("CREATE INDEX IF NOT EXISTS resultsByTag ON results_tags(tag)")

proc findResults(tags: seq[int64], limit: int, offset: int): int64 =
  var s = "SELECT id FROM results WHERE limit = ? AND offset = ?"
  if tags.len == 0:
    s = s & "AND NOT id IN (select result from results_tags)"
  else:
    s = s & "AND id IN (SELECT result FROM results_tags WHERE tag ";
    if tags.len == 1:
      s = s & "= ?"
    else:
      s = s & "IN (" & repeat("?,",tags.len-1) & "?)"
    s = s & " GROUP BY result HAVING count()==?)"
  var st = prepare(s)
  var which = 0
  st.Bind(++which,limit)
  st.Bind(++which,offset)
  for tag in tags:
    st.Bind(++which,tag)
  st.Bind(++which,tags.len)
  return st.getValue()

proc cache*(sql: string, tags: seq[int64], limit: int, offset: int): CheckStmt =
  var name = findResults(tags,limit,offset));
  try:
    var select = prepare("SELECT * FROM resultcache.r" & $name)
    select.step()
    return select
  except NoResults: discard
  withTransaction(db):
    var insert = prepare("INSERT INTO results (limit,offset) VALUES (?,?)")
    insert.Bind(1,limit)
    insert.Bind(2,offset)
    insert.step()
    var result = last_insert_rowid()
    insert = prepare("INSERT INTO results_tags (result,tag) VALUES (?,?)")
    insert.Bind(1,result)
    for tag in tags:
      insert.Bind(2,tag)
      insert.step()
      insert.reset()
    var create = prepare("CREATE TABLE AS resultcache.r" & $result & " " & sql);
    create.step()
  select.get()
  return select

proc doExpire(s: string, tags: seq[int64]) =
  var select = prepare(s)
  var delete = prepare("DELETE FROM results WHERE id IN (" & s & ")");
  var which = 0
  for tag in tags:
    select.Bind(++which,tag)
    delete.Bind(which,tag)
  select.Bind(++which,tags.len)
  delete.Bind(which,tags.len)
  try: select.get()
  except: return
  for _ in select.foreach():
    var result = select.column_int();    
    exec("DROP TABLE resultcache." & $result)
  delete.step()

proc expire*(tags: seq[int64]) =
  # limit and offset don't matter, since the results shift
  var s = "SELECT result FROM results_tags WHERE tag ";
  if tags.len == 1:
    s = s & "= ?";
    doExpire(s,tags)
  else:
    s = s & "IN (" & repeat("?,",tags.len-1) & "?)";
    doExpire(s,tags);
    
