from herpaderp import `++`
from dbconn import
  prepare,
  exec,
  last_insert_rowid,
  conn
from sqldelite import
  Bind,
  maybeValue,
  CheckStmt,
  step,
  NoResults,
  withTransaction,
  get,
  foreach,
  column_int,
  finalize,
  resetStmt
from strutils import repeat

exec("""CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY,
derplimit INTEGER,
derpoffset INTEGER)""")

exec("""CREATE TABLE IF NOT EXISTS results_tags (id INTEGER PRIMARY KEY,
  result NOT NULL REFERENCES results(id) ON DELETE CASCADE ON UPDATE CASCADE,
  tag INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE,
UNIQUE(result,tag))""")

exec("CREATE INDEX IF NOT EXISTS resultsByTag ON results_tags(tag)")

proc bindTags(which: var int, st: CheckStmt, tags: seq[int64]) =
  for tag in tags:
    echo("tag ",tag," ",which)
    st.Bind(++which,tag)
  if tags.len > 1:
    st.Bind(++which,tags.len)

proc findResults(tags: seq[int64], limit: int, offset: int): tuple[value: int64, ok: bool] =
  var s = "SELECT id FROM results WHERE derplimit = ? AND derpoffset = ?"
  if tags.len == 0:
    s = s & " AND NOT id IN (select result from results_tags)"
  else:
    s = s & " AND id IN (SELECT result FROM results_tags WHERE tag ";
    if tags.len == 1:
      s = s & "= ?)"
    else:
      s = s & "IN (" & repeat("?,",tags.len-1) & "?)"
      s = s & " GROUP BY result HAVING count()==?)"
  var st = prepare(s)
  st.resetStmt()
  var which = 0
  st.Bind(1,limit)
  st.Bind(2,offset)
  bindTags(which,st,tags)
  return st.maybeValue()

proc cache*(sql: string, tags: seq[int64], limit: int, offset: int): CheckStmt =
  echo("CACHE ",tags)
  var name = findResults(tags,limit,offset)
  if not name.ok:
    withTransaction(conn):
      var insert = prepare("INSERT INTO results (derplimit,derpoffset) VALUES (?,?)")
      defer: insert.finalize()
      insert.Bind(1,limit)
      insert.Bind(2,offset)
      insert.step()
      var rederp = last_insert_rowid()
      insert.finalize()
      insert = prepare("INSERT INTO results_tags (result,tag) VALUES (?,?)")
      insert.Bind(1,rederp)
      for tag in tags:
        insert.Bind(2,tag)
        insert.step()
        insert.resetStmt()
      echo("CREATE",sql)
      var create = prepare("CREATE TABLE resultcache" & $rederp & " AS " & sql);
      defer: create.finalize()
      var which = 0
      bindTags(which,create,tags)
      create.Bind(++which,limit)
      create.Bind(++which,offset)
      create.step()
    name = findResults(tags, limit, offset)
  return prepare("SELECT * FROM resultcache" & $name.value)

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
    var result = select.column_int(1);
    exec("DROP TABLE resultcache" & $result)
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
