import sqlite3
import strutils

#proc createFunction*(c: PSqlite3, name: string, nArg: int, fnc: Tcreate_function_func_func) =
#  create_function(c,name,nArg,SQLITE_UTF8,nil,fnc,nil,nil);

type CheckDB* = PSqlite3
type CheckStmt* = object
  db: CheckDB
  st: PStmt

type DBError* = ref object of SystemError
  res: cint
  columns: cint
  index: int

proc check(db: CheckDB, res: cint) =
  case(res):
    of SQLITE_OK,SQLITE_DONE,SQLITE_ROW:
      return
    else:
      raise DBError(msg: $db.errmsg())

proc check(st: CheckStmt, res: cint) {.inline.} =
  check(st.db,res)

proc Bind*(st: CheckStmt, idx: int, val: int) =
  st.check(bind_int(st.st,idx.cint,val.cint))

proc Bind*(st: CheckStmt, idx: int, val: string) =
  st.check(bind_text(st.st,idx.cint,val, val.len.cint, nil))

proc step*(st: CheckStmt) =
  st.check(step(st.st))

iterator foreach*(st: CheckStmt): int =
  var i = 0
  while true:
    var res = step(st.st)
    check(st, res)
    if res == SQLITE_ROW:
      yield i
      inc(i)
    elif res == SQLITE_DONE:
      break
  
proc reset*(st: CheckStmt) =
  st.check(reset(st.st))

proc get*(st: CheckStmt) =
  var res = step(st.st)
  if(res == SQLITE_DONE):
    st.reset()
    raise DBError(msg: "No results?")
  st.check(res)

proc column*(st: CheckStmt, idx: int): string =
  var res = column_text(st.st,idx.cint)
  if(res == nil):
    raise DBError(msg: "No column at index $1" % [$idx], index: idx, columns: column_count(st.st))
  return $res

proc column_int*(st: CheckStmt, idx: int): int =
  return column_int(st.st,idx.cint)

proc open*(location: string, db: var CheckDB) =
  var res = sqlite3.open(location,db.PSqlite3)
  assert(db != nil)
  if (res != SQLITE_OK):
    raise DBError(msg: "Could not open")

template withPrep*(st, derpdb, sql: expr, actions: stmt): stmt {.immediate.} =
  var st: CheckStmt
  var ssql = sql
  st.db = derpdb
  echo("b4",ssql,ssql.len,' ',st.db==nil)
  var res = prepare_v2(st.db,ssql,ssql.len.cint,st.st,nil)
  echo("result ",res,"==",SQLITE_OK,st.st==nil)
  derpdb.check(res)
  try:
    actions
  finally:
    check(st,finalize(st.st))  

template withTransaction*(db: expr, actions: stmt) =
  withPrep(begin,db,"BEGIN"):
    withPrep(commit,db,"COMMIT"):
      withPrep(rollback,db,"ROLLBACK"):
        begin.step()
        try:
          actions
          commit.step()
        except:
          rollback.step()
          raise

proc exec*(db: CheckDB, sql: string) =
  withPrep(st,db,sql):
    db.check(step(st.st))

proc getValue*(st: CheckStmt): int =
  assert(1==column_count(st.st))
  defer: st.db.check(reset(st.st))
  var res = step(st.st)
  case res:
    of SQLITE_ROW:
      return column_int(st.st,0);
    else:
      raise DBError(msg:"Didn't return a single row",res:res)

proc getValue*(db: CheckDB, sql: string): int =
  withPrep(st,db,sql):
    return st.getValue()
