import sqldelite,strutils

const onequery = "SELECT medium FROM media_tags WHERE tag = (SELECT id FROM tags WHERE name = ?)\n";

var conn: CheckDB

open("pics.sqlite",conn)

proc makeQuery(posi,nega) string:
  if posi.len == 0:
    result = "SELECT media FROM media"
  else:
    for tag in posi:
      if result != "":
        result = result & " INTERSECT "
      result = result & oneresult
  for tag in nega:
    if result != "":
      result = result & " EXCEPT "
    result = result & oneresult
  result = "SELECT id,name FROM media WHERE id IN (" & result & ")"
  result = result & " ORDER BY added DESC"

  
proc list*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[medium: int,title: string]] =
  var query = makeQuery(posi,nega)
  query = query & " LIMIT ?"
  query = query & " OFFSET ?"
  withPrep(st,conn,query):
    var which = 1
    for tag in posi:
      st.Bind(which,tag)
      inc(which)
    for tag in nega:
      st.Bind(which,tag)
      inc(which)
    st.Bind(which,limit)
    inc(which)
    st.Bind(which,offset)
    for _ in st.foreach():
      var medium: int = column_int(st,0)
      var title: string = column(st,1)
      add(result,(medium: medium, title: title))
