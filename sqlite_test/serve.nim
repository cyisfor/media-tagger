import asynchttpserver, asyncnet, asyncdispatch, strtabs, strutils, math

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
    var uri = parseUri(req.url)
    var tags = split(uri,'/');
    var posi: seq[string];
    var nega: seq[string];
    for tag in tags:
      if tag[0] == '-':
        add(nega,tag[1..])
      else:
        add(posi,tag)
    var html = "<!DOCTYPE html><html><head><title>Drep</title></head><body>"
    db.list(posi,nega,0x20,0x20*page) do (medium: int, title: string):
      add(html,q"{<a href="/art/~page/}" & toHex(medium) & q"{">
<img title="}" & title & q"{" src="/thumb/}" & toHex(medium) & q"{" />
</a>\n}")
    add(html,"</body></html>")
    await req.respond(Http200,html)

var server = newAsyncHttpServer()

waitFor server.serve(Port(9878), handle)
