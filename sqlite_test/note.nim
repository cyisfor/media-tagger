type Notepad* = ref object of RootObj
  location: bool
  minlevel: int

var Notepad root

root.location = true

proc note(level: string, format: string, args: varargs[string, `$`]) {.noSideEffect.} =
  var s: string
  if root.location:
    var frame = getFrame().prev
    s = "("
    if root.byProcedure:
      s = s & frame.procname
    else:
      s = s & frame.filename
      s = s & ":" & $(frame.line) & ") "
      s = s & level & ": " & strutils.format(format, args))
  else:
    s = level & ": " & strutils.format(format, args)
    debugEcho(s)

from macros import
  bindSym,
  toStrLit,
  newStrLitNode,
  newNimNode,
  nnkStmtList

macro setup(levelvar: expr,
            minlevel: expr,
            names: stmt): stmt =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  var enunames: nnkEnumTy(nnkEmpty())
  for name in names:
    add(enunames,name)
  add(result,nnkTypeDef(levelvar,
                        nnkEmpty(),
                        enunames))
  # root.minlevel = info
  add(result,nnkAsgn(nnkIdent(!"root"),minlevel))

  for name in names:
    # template info*(...)
    add(result,nnkTemplateDef(nnkPostfix(nnkIdent(!"*"), name), # export
                              nnkEmpty(), # no rewriting
                              nnkEmpty(), # not generic
                              # (format: expr, args: varargs[expr])
                              nnkFormalParams(
                                nnkEmpty(), # return none
                                nnkIdentDefs(
                                  nnkIdent(!"format"),
                                  nnkIdent(!"expr"),
                                  nnkEmpty()),
                                nnkIdentDefs(
                                  nnkIdent(!"args"),
                                  nnkBracketExpr(
                                    nnkIdent(!"varargs"),
                                    nnkIdent(!"expr")))),
                              nnkEmpty(), # no {.macros.}
                              nnkEmpty(), # reserved
                              # if info > root.minlevel: note(format,args)
                              nnkStmtList(
                                nnkIfStmt(
                                  nnkElifBranch(
                                    nnkInfix(
                                      nnkIdent(">="),
                                      name,
                                      nnkDotExpr(
                                        nnkIdent(!"root")
                                        nnkIdent(!"minlevel"))),
                                    nnkCall(nnkIdent(!"note"),
                                            nnkIdent("format"),
                                            nnkIdent("args")))))))


setup(Level,info):
  spam
  debug
  chatty
  info
  warn
  error
  always

info("test $1","hi")
