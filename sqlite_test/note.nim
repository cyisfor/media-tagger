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
  bindSym,
  toStrLit,
  newStrLitNode,
  newNimNode,
  nnkStmtList,
  nnkEnumTy,
  nnkEmpty,
  nnkTypeDef,
  nnkAsgn,
  nnkTemplateDef,
  add

macro setup(pieces: stmt): stmt =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  var names = pieces[0][2..high(names)]

  # enum
  add(result,pieces[0])
  
  # root.minlevel = info
  add(result,pieces[1])

  for name in names:
    # template info*(...)
    templatederp = deepCopy(pieces[2])
    # (template 0:(postfix (ident (*)) NAME)
    #  1:(rewriting) 2:(generics)
    #  3:(params) 4:(macros) 5:(reserved)
    #  6:(statements
    #      0:(if 0:(elif >= NAME root.minlevel) 1:(call 0:note 1:NAME format args))))
    templatederp[0][0][1] = name
    var stmtlist = templatederp[6]
    var theelif = stmtlist[0][0]
    theelif[1] = name
    stmtlist[1][1] = name
    add(result,templatederp)    

setup(Level,info):
  type Level = enum
    spam
    debug
    chatty
    info
    warn
    error
    always

  root.minlevel = whatever

  template somename*(format: expr, args: varargs[expr]) =
    note(somenamewhatever, format, args)
  
info("test $1","hi")
