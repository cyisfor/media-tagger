from strutils import toLower

type Level = enum
  SPAM
  DEBUG
  CHATTY
  INFO
  WARN
  ERROR
  ALWAYS

type Notepad* = ref object of RootObj
  location: bool
  byProcedure: bool
  minlevel: Level

var root: Notepad = new Notepad

root.location = true
root.byProcedure = false
root.minlevel = INFO

proc makesrc(): string =
  var frame = getFrame().prev
  if root.byProcedure:
    return $frame.procname
  else:
    return $frame.filename & ":" & $(frame.line)


proc note(srcname: string, level: string, format: string, args: varargs[string, `$`]) =
  var s: string
  if root.location:
    s = "(" & srcname & ") "
    s = s & level & ": " & strutils.format(format, args)
  else:
    s = level & ": " & strutils.format(format, args)
  debugEcho(s)

from macros import
  newNimNode,
  newIdentNode,
  nnkStmtList,
  treeRepr,
  toStrLit,
  newStrLitNode,
  quote,
  copyChildrenTo,
  parseStmt
    
template setup(): stmt {.immediate.} =
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  for level in low(Level)..high(Level):
    var ident = $level
    var name = "\"" & toLower(ident) & "\"";
    template `name`(format: expr, args: varargs[string,`$`]) =
        if root.minlevel > `ident`:
          note(makesrc(),`namestr`, format, args)
setup()

info("inf $1","2")

template DERP*(format: expr, args: varargs[expr]) =
  if root.minlevel > HERPDERP:
    note("DERPSTR", format, args)

    
