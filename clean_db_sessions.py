from do_core.sql.sql_server import get_session
from do_core.sql.graph import ActionModel, EndpointModel, EndpointResourceModel, FlowRuleModel, GraphModel, MatchModel, OpenstackNetworkModel, OpenstackSubnetModel, PortModel, VNFInstanceModel 
from do_core.sql.session import SessionModel

session = get_session()
session.query(ActionModel).delete()
session.query(EndpointModel).delete()
session.query(EndpointResourceModel).delete()
session.query(FlowRuleModel).delete()
session.query(GraphModel).delete()
session.query(MatchModel).delete()
session.query(OpenstackNetworkModel).delete()
session.query(OpenstackSubnetModel).delete()
session.query(PortModel).delete()
session.query(VNFInstanceModel).delete()
session.query(SessionModel).delete()

print ("Database sessions deleted")
