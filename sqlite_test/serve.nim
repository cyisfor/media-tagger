import asynchttpserver, asyncnet, asyncdispatch, strtabs, strutils, math
import uri
from cgi import decodeUrl
import times
import db,sqldelite

proc mylog(x: BiggestInt): float = 
  return math.ln(toFloat(cast[int](x))) / math.ln(0x10)

proc toHex(x: BiggestInt): string =
  if x == 0: return "0"
  var len: int = toInt(math.floor(mylog(x)))+1
  return toHex(x,len)

assert(toHex(0x8)=="8")
assert(toHex(0x10)=="10")
assert(toHex(0x11)=="11")
assert(toHex(0xfff)=="FFF")

proc chop(s: string, c: char): (string,string) =
  var where = s.find(c)
  if(where == -1):
    return (s,"")
  return (s[0..where-1],s[where+1..s.len])

proc handle(req: Request, mode: string, path: string) {.async.} =
  case mode
  of "page":
    echo("PATH ",path)
    var id: int
    if path[path.len-1] == '/':
      id = parseHexInt(path[0..path.len-2])
    else:
      id = parseHexInt(path)
    var Type, name, tags: string
    var nope = false
    try:
      let derp = db.page(id)
      Type = derp[0]
      name = derp[1]
      tags = derp[2]
    except sqldelite.NoResults:
      nope = true
    if nope:
      await req.respond(Http500,"No page by that id " & $id)
      return
    await req.respond(Http200,format("""<html><head><title>Page for $id</title></head><body><p><a href="/media/$id/$meta"><img src="/media/$id/$meta" /></a><p>$tags</p></body></html>\n""",["id", toHex(id).toLower(), "meta", Type & "/" & name, "tags", tags]))
  else:
   await req.respond(Http500,"No mode derp " & mode)
   

const prefix = "testart/"

type TimeTest = tuple
  start: float
  name: string

proc startTest(name: string): TimeTest =
  return (times.cpuTime(),name)
proc done(lastTime: TimeTest) =
  var curTime = times.cpuTime()
  echo(lastTime.name," elapsed ",curTime-lastTime.start)

proc handle(req: Request) {.async.} =
  case req.reqMethod
  of "get":
    var path = req.url.path[1..req.url.path.len];
    if path[0..prefix.len-1] == prefix:
      path = path[prefix.len..path.len]
    if path[0] == '~':
      var (mode, path) = chop(path[1..path.len],'/')
      await handle(req,mode,path)
      return
    var tags = split(path,'/')
    echo("path ",req.url.path)
    echo("tags ",escape($tags))
    if tags.len > 1 and tags[0] == "art":
      tags = tags[1..tags.len]
      
    var posi: seq[string] = @[];
    var nega: seq[string] = @[];
    for tag in tags:
      var derp = decodeUrl(tag)
      echo("tag ",escape(derp))
      if derp == nil or derp == "":
        continue
      if derp[0] == '-':
        add(nega,derp[1..derp.len])
      else:
        add(posi,derp)
    var page = 3

    var choonks = ""
    proc sendChunk(cli: AsyncSocket, chunk: string) {.async.} =
      choonks = choonks & chunk
    proc endChunks(cli: AsyncSocket) {.async.} =
      choonks = choonks & "\n"
      await req.respond(Http200,choonks)

    await sendChunk(req.client, "<!DOCTYPE html><html><head><title>Drep</title></head><body>")
    await sendChunk(req.client,"<p>" & req.url.path & "</p><p>")
    var herp: seq[tuple[medium: int64,title: string]];
    try:
      var test = startTest("list")
      herp = db.list(posi,nega,0x20,0x20*page)
      test.done()
    except:
      echo("DERRRRP ",getCurrentExceptionMsg())
      raise
    for medium,title in items(herp):
      await sendChunk(req.client,format("""{<a href="/art/~page/$1">
      <img title="$2" src="/thumb/$1">
</a>""",toHex(medium).toLower(),title))

    await sendChunk(req.client,"</p><p>")
    if false:
      await endChunks(req.client)
      return
    echo("yay?")
    var test = startTest("related")
    for name,count in items(db.related(posi,nega,8,0)):
      await sendChunk(req.client,name & ":" & $count & " ")
    test.done()
    await sendChunk(req.client,"</p></body></html>\n")
    await endChunks(req.client)
  else:
    await req.respond(Http500,"uhh")

var server = newAsyncHttpServer()
waitFor server.serve(Port(9878), handle)
