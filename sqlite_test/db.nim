import strutils
from sqldelite import column_int, column
from dbconn import prepare, last_insert_rowid
from resultcache import nil

const onequery = "SELECT medium FROM media_tags WHERE tag "

proc equalOrInTags(len: int): string =
  result = ""
  if len == 1:
    result = result & "= (SELECT id FROM tags WHERE name = ?)\n";
  else:
    result = result & "IN (SELECT id FROM tags WHERE name IN (" & repeat("?,",len-1) & "?))\n"

proc makeQuery(posi: seq[string],nega: seq[string]): string =
  result = ""
  if posi.len == 0:
    if nega.len == 0:
      result = "SELECT medium FROM media_tags"
    else:
      # sigh
      result = "SELECT medium FROM media_tags WHERE NOT tag " & equalOrInTags(nega.len)    
  else:
    result = onequery & equalOrInTags(posi.len) &
      " GROUP BY medium" &
      " HAVING(count()==?)"
    if nega.len > 0:
      result = result & " EXCEPT\n" & onequery & equalOrInTags(nega.len)

proc bindTags(st: CheckStmt, posi: seq[string],nega: seq[string]): int =
  var which = 0
  if posi.len > 0:
    for tag in posi:
      st.Bind(++which,tag)
    st.Bind(++which,posi.len) # HAVING
  for tag in nega:
    st.Bind(++which,tag)
  return which

var derpS = prepare("SELECT id FROM tags WHERE name = ?")
var derpI = prepare("INSERT INTO tags (name) VALUES (?)")

proc findTag*(name: string): int =
  derpS.Bind(1,name)
  try:
    return derpS.getValue()
  except NoResults:
    derpI.Bind(1, name)
    derpI.step()
    return last_insert_rowid()
  finally:
    derpS.reset()
    derpI.reset() # ehhh

proc findTags(tags seq[string]): seq[int] =
  result = newSeq[int](tags.len)
  for i in 0..tags.len:
    result[i] = findTag(tags[i])
    
proc list*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[medium: int,title: string]] =
  return list(findTags(posi),findTags(nega), limit, offset)

proc list*(posi: seq[int],nega: seq[int], limit: int, offset: int): seq[tuple[medium: int,title: string]] =
  result = @[]
  var query = "SELECT id,name FROM media INNER JOIN (" & makeQuery(posi,nega) & ") AS derp ON derp.medium = media.id GROUP BY media.id"
  echo("query ",query)
  query = query & " ORDER BY added DESC"
  query = query & " LIMIT ?"
  query = query & " OFFSET ?"

  var st = resultcache.cache(query,concat(posi,nega),limit,offset)
  let threshold = 0
  var which = bindTags(st,posi,nega)
  st.Bind(++which,limit)
  st.Bind(++which,offset)
  for _ in st.foreach():
    var medium: int = column_int(st,0)
    var title: string = column(st,1)
    add(result,(medium: medium, title: title))

var pageStatement = prepare("SELECT type, name, (select group_concat(name,?) from tags inner join media_tags on tags.id = media_tags.tag where media_tags.medium = media.id) FROM media WHERE id = ?")
    
proc page*(id: int): (string,string,string) =
    echo("IDE ",id)
    pageStatement.Bind(1,", ")
    pageStatement.Bind(2,id)
    pageStatement.get()
    return (column(pageStatement,0),
            column(pageStatement,1),
            column(pageStatement,2))

proc getRelated(st: CheckStmt): seq[tuple[tag: string, count: int]] =
  result = @[]
  for _ in st.foreach():
    var tag = column(st,0)
    var count = column_int(st,1)
    add(result,(tag: tag, count: count))

var relst = prepare("SELECT name,(select count() from media_tags where tag = tags.id) as num from tags order by num DESC LIMIT ? OFFSET ?")
    
proc related*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[tag: string,count: int]] =
  var query: string
  if posi.len == 0:
    # too expensive to try related tags for only negative tags
    relst.Bind(1,limit)
    relst.Bind(2,offset)
    return getRelated(relst)

  query = "SELECT (select name from tags where id = tag) AS tag,count() AS num FROM media_tags"
  if posi.len > 0 or nega.len > 0:
    query = query & " INNER JOIN (" & makeQuery(posi,nega) & ") AS med ON med.medium = media_tags.medium"
    query = query & " GROUP BY tag ORDER BY num DESC LIMIT ? OFFSET ?"
    
  var st = prepare(query)
  var which = bindTags(st,posi,nega)
  st.Bind(++which,limit)
  st.Bind(++which,offset)
  return getRelated(st)
