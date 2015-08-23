import sqldelite,strutils
var conn: CheckDB

const onequery = "SELECT medium FROM media_tags WHERE tag = (SELECT id FROM tags WHERE name = ?)\n";

proc startdb*() =
  open("pics.sqlite",conn)

proc list*(posi: seq[string],nega: seq[string], limit: int, offset: int, handle: proc(medium: int,title: string)) =
  var query = ""
  for tag in posi:
    if query != "":
      query = query & " INTERSECT "
    query = query & onequery
  if nega.len > 0:
    for tag in nega:
      if query != "":
        query = query & " EXCEPT "
      query = query & onequery
  query = query & " LIMIT ?"
  query = query & " OFFSET ?"
  query = "SELECT id,name FROM media WHERE id IN (" & query & ")"
  var herpderp = posi
  var nerp = nega
  withPrep(conn,query) do (st: CheckStmt):
    var which = 0
    for tag in herpderp:
      st.Bind(which,tag)
      which += 1
    for tag in nerp:
      st.Bind(which,tag)
      which += 1
    st.Bind(which,limit)
    which += 1
    st.Bind(which,offset)
    which += 1
    st.foreach() do ():
      var medium: int = column_int(st,0)
      var title: string = column(st,1)
      handle(medium,title)
