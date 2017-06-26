import requests, json
# This Script is used to delete a deployed graph within the Openstack-DO. Change the "orchestrator_endpoint" variable with the right FG id
username = "admin"
password = "admin"
tenant = "admin"
orchestrator_endpoint = "http://127.0.0.1:9200/NF-FG/40400"
headers = {'Content-Type': 'application/json', 'X-Auth-User': username, 'X-Auth-Pass': password, 'X-Auth-Tenant': tenant}

authenticate = { "username": username, "password": password }
print(authenticate)

r = requests.post('http://127.0.0.1:9200/login', json.dumps(authenticate))
print(r.text)
headers['X-Auth-Token'] = r.text

resp = requests.delete(orchestrator_endpoint, headers=headers)
resp.raise_for_status()
