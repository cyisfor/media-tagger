import sqldelite,strutils

const onequery = "SELECT medium FROM media_tags WHERE tag IN (SELECT id FROM tags WHERE name = ?)\n";

var conn: CheckDB

open("pics.sqlite",conn)

proc makeQuery(posi: seq[string],nega: seq[string]): string =
  result = ""
  if posi.len == 0:
    result = "SELECT medium FROM media_tags"
  else:
    for tag in posi:
      if result != "":
        result = result & " INTERSECT "
      result = result & onequery
  for tag in nega:
    if result != "":
      result = result & " EXCEPT "
    result = result & onequery

template `++`(n: expr): expr {.immediate.} =
  n = n + 1
  n

proc bindTags(st: CheckStmt, posi: seq[string],nega: seq[string]): int =
  var which = 0
  for tag in posi:
    st.Bind(++which,tag)
  for tag in nega:
    st.Bind(++which,tag)
  return which
  
proc list*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[medium: int,title: string]] =
  result = @[]
  var query = "SELECT id,name FROM media INNER JOIN (" & makeQuery(posi,nega) & ") AS derp ON derp.medium = media.id GROUP BY media.id"
  echo("query ",query)
  query = query & " ORDER BY added DESC"
  query = query & " LIMIT ?"
  query = query & " OFFSET ?"

  withPrep(st,conn,query):
    let threshold = 0
    var which = bindTags(st,posi,nega)
    st.Bind(++which,limit)
    st.Bind(++which,offset)
    for _ in st.foreach():
      var medium: int = column_int(st,0)
      var title: string = column(st,1)
      add(result,(medium: medium, title: title))

proc page*(id: int): (string,string,string) =
  withPrep(st,conn,"SELECT type, name, (select group_concat(name,?) from tags inner join media_tags on tags.id = media_tags.tag where media_tags.medium = media.id) FROM media WHERE id = ?"):
    echo("IDE ",id)
    st.Bind(1,", ")
    st.Bind(2,id)
    st.get()
    return (column(st,0),column(st,1),column(st,2))
      
proc related*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[tag: string,count: int]] =
  var query: string
  if posi == nil and nega == nil:
    query = "SELECT (select name from tags where id = tag),count(medium) AS num FROM media_tags GROUP BY tag ORDER BY num DESC LIMIT ? OFFSET ?"
  else:
    query = "SELECT (select name from tags where id = tag) AS tag,count(medium) AS num FROM media_tags"
    if posi.len > 0 or nega.len > 0:
      query = query & "WHERE medium IN (" & makeQuery(posi,nega) & ")"
    query = "SELECT tag,num FROM (" & query & ") AS derp"
    query = query & " WHERE num > ? GROUP BY tag ORDER BY num DESC LIMIT ? OFFSET ?"
  result = @[]
  withPrep(st,conn,query):
    let threshold = 4
    var which = bindTags(st,posi,nega)
    st.Bind(++which,threshold)
    st.Bind(++which,limit)
    st.Bind(++which,offset)
    for _ in st.foreach():
      var tag = column(st,0)
      var count = column_int(st,1)
      add(result,(tag: tag, count: count))
