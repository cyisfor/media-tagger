import asynchttpserver, asyncnet, asyncdispatch, strtabs, strutils, math
import uri
import db

# SIGH...
proc sendStatus(client: AsyncSocket, code: HttpCode, status: string): Future[void] =
  client.send("HTTP/1.1 " & $code & " " & status & "\c\L")

proc toHex(x: BiggestInt): string =
  var len: int = math.round(math.ln(toFloat(cast[int](x))) / math.ln(10)) + 1
  return toHex(x,len)

proc sendChunk(client: AsyncSocket, hunk: string): Future[void] =
  var chunk = toHex(len(hunk)) & "\c\L" & hunk & "\c\L"
  echo(escape(chunk))
  return send(client,chunk)

proc endChunks(client: AsyncSocket): Future[void] =
  return send(client,"0\c\L\c\L")
  
proc handle(req: Request) {.async.} =
  case req.reqMethod
  of "get":
    echo(req.url.path)
    var tags = split(req.url.path,'/');
    echo(tags)
    var posi: seq[string] = newSeq(0);
    var nega: seq[string] = newSeq(0);
    for tag in tags:
      if tag == nil:
        continue
      if tag[0] == '-':
        add(nega,tag[1..tag.len])
      else:
        add(posi,tag)
    var page = 3

    await req.client.sendStatus(Http200, "Yay?")
    await req.sendHeaders(newStringTable({"Transfer-Encoding": "chunked"}))
    await req.client.send("\c\L")

    echo(posi)
    await sendChunk(req.client, "<!DOCTYPE html><html><head><title>Drep</title></head><body>")
    await sendChunk(req.client,"<p>" & req.url.path & "</p>")
    for medium,title in db.list(posi,nega,0x20,0x20*page):
      await sendChunk(req.client,format("""{<a href="/art/~page/$1">
      <img title="$2" src="/thumb/$1/">
</a>""",toHex(medium),title))
    await sendChunk(req.client,"</body></html>")
    await endChunks(req.client)
  else:
    await req.respond(Http500,"uhh")

var server = newAsyncHttpServer()

waitFor server.serve(Port(9878), handle)
