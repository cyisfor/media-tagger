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

var root: Notepad

root.location = true
root.byProcedure = false
root.minlevel = INFO

proc note(level: string, format: string, args: varargs[string, `$`]) =
  var s: string
  if root.location:
    var frame = getFrame().prev
    s = "("
    if root.byProcedure:
      s = s & $frame.procname
    else:
      s = s & $frame.filename
      s = s & ":" & $(frame.line) & ") "
      s = s & level & ": " & strutils.format(format, args)
  else:
    s = level & ": " & strutils.format(format, args)
    debugEcho(s)
