# This script can be used to send an NF-FG to the OpenStack domain orchestrator.
# You can execute it through the following command
# $ python put_graph.py

import requests, json

# Write here the cretential to be used for authentication
username = "admin"
password = "admin"
tenant = "admin"

# Write here the NF-FG that you want to deploy

# This NF-FG simply deploy a VNF connected to VLAN endpoint
nffg = \
{
  "forwarding-graph": {
    "id": "123",
    "name": "Demo Graph 1",
    "VNFs": [
      {
        "id": "00000001",
        "name": "client",
        "vnf_template":"IU9LBT",
       "functional-capability":"bridge",
        "ports": [
          {
            "id": "inout:0"
          }
        ]
      }
    ],
    "end-points": [
      {
        "type": "vlan",
        "vlan": {
          "node-id": "of:000034dbfd3c1140",
          "vlan-id": "297",
          "if-name": "5097"
        },
        "id": "00000001"
      }
    ],
    "big-switch": {
      "flow-rules": [
        {
          "match": {
            "port_in": "vnf:00000001:inout:0"
          },
          "actions": [
            {
              "output_to_port": "endpoint:00000001"
            }
          ],
          "priority": 40001,
          "id": "1"
        },
        {
          "match": {
            "port_in": "endpoint:00000001"
          },
          "actions": [
            {
              "output_to_port": "vnf:00000001:inout:0"
            }
          ],
          "priority": 40001,
          "id": "2"
        }
      ]
    }
  }
}

# Write here the URL to be used to reach the domain orchestrator and deploy the new graph
orchestrator_endpoint = "http://127.0.0.1:9200/NF-FG/myGraph"

# Do not change the following code
headers = {'Content-Type': 'application/json', 'X-Auth-User': username, 'X-Auth-Pass': password, 'X-Auth-Tenant': tenant}

authenticate = { "username": username, "password": password }

r = requests.post('http://127.0.0.1:9200/login', json.dumps(authenticate))
print(r.text)
headers['X-Auth-Token'] = r.text

resp = requests.put(orchestrator_endpoint, json.dumps(nffg), headers=headers)
resp.raise_for_status()
