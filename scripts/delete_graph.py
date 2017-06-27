# This script can be used to delete an NF-FG from the OpenStack domain.
# You can execute it through the following command
# $ python delete_graph.py

import requests, json

# Write here the cretential to be used for authentication
username = "admin"
password = "admin"
tenant = "admin"

# Write here the URL to be used to reach the domain orchestrator in order to delete the graph
orchestrator_endpoint = "http://127.0.0.1:9200/NF-FG/myGraph"

# Do not change the following code

headers = {'Content-Type': 'application/json', 'X-Auth-User': username, 'X-Auth-Pass': password, 'X-Auth-Tenant': tenant}

authenticate = { "username": username, "password": password }

r = requests.post('http://127.0.0.1:9200/login', json.dumps(authenticate))
print(r.text)
headers['X-Auth-Token'] = r.text

resp = requests.delete(orchestrator_endpoint, headers=headers)
resp.raise_for_status()
