from orchestrator_core.sql.sql_server import get_session
from orchestrator_core.sql.user import UserModel
from sqlalchemy.sql import func
import sys


session = get_session()
query = session.query(func.max(UserModel.id).label("max_id"))
result = query.one()
newID = int(result.max_id) + 1
name = input("User name:")
pwd = input("Password:")
result = session.query(UserModel).filter_by(name=name).first()
if result is not None:
	print ("User already created")
	sys.exit()
user = UserModel()
user.id = newID
user.name = name
user.password = pwd
session.add(user)
session.flush()
print ("User created")
