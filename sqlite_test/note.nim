from strutils import nil

type Notepad* = ref object of RootObj
  location: bool
  byProcedure: bool
  minlevel: int

var root: Notepad

root.location = true
root.byProcedure = false

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

from macros import
  newNimNode,
  nnkStmtList,
  add,
  `[]`,
  `[]=`,
  `$`,
  len,
  dumpTree,
  findChild,
  ident=,
  toStrLit

macro setup(pieces: stmt): stmt {.immediate.} =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  add(result,pieces[0])
  add(result,pieces[1])
  echo(pieces)

  var i = 2
  while i < len(pieces[0]):
    var name = pieces[0][i]
    i = i + 1
    # template info*(...)
    var templatederp = pieces[2]

    # (template 0:(postfix (ident (*)) NAME)
    #  1:(rewriting) 2:(generics)
    #  3:(params) 4:(macros) 5:(reserved)
    #  6:(statements
    #      0:(if 0:(elif >= NAME root.minlevel) 1:(call 0:note 1:NAME format args))))
    ident=(findChild(templatederp,
                     it.kind == nnkIdent and
                     it.ident == "NAME"),
           name)
    ident=(findChild(templatederp,
                     it.kind == nnkIdent and
                     it.ident == "NAME_STR"),
           toStrLit(name))
    add(result,templatederp)

setup():
  type Level = enum
    spam
    debug
    chatty
    info
    warn
    error
    always

  root.minlevel = info

  template NAME*(format: expr, args: varargs[expr]) =
    note(NAME_STR, format, args)
  
info("test $1","hi")
