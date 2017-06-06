import requests, json

username = "admin"
password = "admin"
tenant = "admin"
orchestrator_endpoint = "http://127.0.0.1:9200/NF-FG/2"
headers = {'Content-Type': 'application/json', 'X-Auth-User': username, 'X-Auth-Pass': password, 'X-Auth-Tenant': tenant}

authenticate = { "username": username, "password": password }
print(authenticate)

r = requests.post('http://127.0.0.1:9200/login', json.dumps(authenticate))
print(r.text)
headers['X-Auth-Token'] = r.text
data_file = open('/home/roberto/frog4-openstack-do-onos/SecondGraph.json')
nffg_dict3 = json.load(data_file)

resp = requests.put(orchestrator_endpoint, json.dumps(nffg_dict3), headers=headers)
resp.raise_for_status()
