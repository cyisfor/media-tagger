import sqldelite
var conn*: CheckDB
open("pics.sqlite",conn)

proc prepare*(sql: string): CheckStmt =
  return prepare(conn,sql)

proc last_insert_rowid(): int64 =
  return last_insert_rowid(conn)

proc exec*(sql: string) =
  exec(conn,sql)
