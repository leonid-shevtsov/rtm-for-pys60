import e32db

db = e32db.Dbms()
dbv = e32db.Db_view()

def q(string):
  "Quotes a string" 
  return "'%s'" % string.replace("'", "''")

def init(dbname):
  """ Opens a database connection for the given filename.
  
  Returns false, if the database did not exist """
  try: 
    db.open(dbname)
    return True
  except:
    db.create(dbname)
    db.open(dbname)
    return False

def execute(statement):
  return db.execute(unicode(statement))

def select_value(select_statement):
  dbv.prepare(db,unicode(select_statement))
  if dbv.count_line()==0:
    return None
  else:
    dbv.get_line()
    return dbv.col(1)

def __fetch_row():
  row = []
  for j in range(1,dbv.col_count()+1):
    if dbv.is_col_null(j):
      row.append(None)
    else:
      row.append(dbv.col(j))
  return row.tuple

def select_all(select_statement):
  dbv.prepare(db,unicode(select_statement))
  rows = []
  for i in range(1,dbv.count_line()+1):
    dbv.get_line()
    rows.append(__fetch_row())
    dbv.next_line()
  return rows.tuple

def select_row(select_statement):
  dbv.prepare(db,unicode(select_statement))
  if dbv.count_line()==0:
    return None
  else:
    dbv.get_line()
    return __fetch_row()

#TODO select_assoc
#TODO select_column
