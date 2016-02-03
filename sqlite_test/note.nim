type Notepad* = ref object of RootObj
  location = false
  minlevel: int = 2 # ehhhh

var Notepad root

from macros import
  bindSym,
  toStrLit,
  newStrLitNode,
  newNimNode,
  nnkStmtList
  
macro setup(level: expr names: expr, notefunc: stmt): stmt =
  result = newNimNode(nnkStmtList)
  add(result,nnkTypeDef(level,nnkEmpty(),
                        nnkEnumTy(nnkEmpty(),
                                  names)))
  add(result,notefunc)
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
                                      nnkIdent(">"),
                                      name,
                                      nnkDotExpr(
                                        nnkIdent(!"root")
                                        nnkIdent(!"minlevel"))),
                                    nnkCall(nnkIdent(!"note"),
                                            nnkIdent("format"),
                                            nnkIdent("args")))))))
                                    
                                               
setup(Level,[
  spam,
  debug,
  chatty,
  info,
  warn,
  error,
  always]):      
  
  proc note(format: string, args: varargs[string, `$`]) {.noSideEffect.} =
    var s: string
    if root.location:
      var frame = getFrame().prev
      s = "("
      if root.byProcedure:
        s = s & frame.procname
      else:
        s = s & frame.filename
      s = s & ":" & $(frame.line) & ") "
      s = s & strutils.format(format, args))
    else:
      s = strutils.format(format, args)
    debugEcho(s)



  
