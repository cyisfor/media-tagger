from sqldelite import openSqlite, prepare, exec, CheckDB, CheckStmt, last_insert_rowid
var conn*: CheckDB = openSqlite("pics.sqlite")

proc prepare*(sql: string): CheckStmt =
  return prepare(conn,sql)

proc last_insert_rowid*(): int64 =
  return last_insert_rowid(conn)

proc exec*(sql: string) =
  exec(conn,sql)

exec("PRAGMA foreign_keys = ON")
assert(conn!=nil)

