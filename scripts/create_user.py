from orchestrator_core.sql.sql_server import get_session
from orchestrator_core.sql.user import UserModel, TenantModel
from sqlalchemy.sql import func
import sys


session = get_session()
query = session.query(func.max(UserModel.id).label("max_id"))
result = query.one()
newID = int(result.max_id) + 1
query = session.query(func.max(TenantModel.id).label("max_id"))
result = query.one()
newTenantID = int(result.max_id) + 1
tenant = input("Tenant name:")
name = input("User name:")
pwd = input("Password:")
result = session.query(UserModel).filter_by(name=name).first()
if result is not None:
	print ("User already created")
	sys.exit()
result = session.query(TenantModel).filter_by(name=tenant).first()
if result is None:
	newTenant = TenantModel()
	newTenant.id = newTenantID
	newTenant.name = tenant
	newTenant.description = "Tenant description"
	session.add(newTenant)
else:
	newTenantID = result.id
user = UserModel()
user.id = newID
user.name = name
user.password = pwd
user.tenant_id = newTenantID
session.add(user)
session.flush()
print ("User created")
