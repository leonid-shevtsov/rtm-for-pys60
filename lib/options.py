import db

def init():
  db.execute("CREATE TABLE options (name VARCHAR, value VARCHAR)")


def get_option(name):
  return db.select_value(u"SELECT value FROM options WHERE name=%s" % db.q(name))

def set_option(name, value):
  if get_option(name)==None:
    db.execute(u"INSERT INTO options (name,value) VALUES (%s,%s)" % (db.q(name), db.q(value)))
  else:
    db.execute(u"UPDATE options SET value=%s WHERE name=%s" % (db.q(value),db.q(name)))

