# OpenStack Domain Orchestrator
This orchestrator controls an OpenStack domain. It is able to deploy service graphs according to the NF-FG used throghout the FROG4 architecture.
In addition to the creation of NFV service chains it allows to steer traffic between an OpenStack port to another OpenStack port or to an external port and viceversa (e.g., a port that connects to the user located outside the OpenStack domain).
This result is achieved by interacting with the SDN controller which in turn has to be configured as the mechanism driver of the OpenStack's Neutron module. 

Currently this domain orchestrator works with OpenStack Mitaka and OpenDaylight Beryllium as Neutron driver.

## REST API

This domain orchestrator offers a REST API which is shared among all the domain orchestrators of the FROG4 architecture.

REST interface provides several urls to authenticate, to send/get/delete a graph, to get the status of a graph.

#### Basic authentication
This step is needed to retrieve a token which will be used into all the operative requests. 
```
	[POST]
	Url: '/login'
	Content-Type: application/json
	Data: { "username":"admin", "password":"admin" }
```
Response is the token:
```
	797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```

#### Send a new graph or update an existent graph
```
	[PUT]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
	Content-Type: application/json
	Data: { "forwarding-graph": { "id": "12345", "name": "GraphName", ... } }
```

#### Get a graph
```
	[GET]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```
Response:
```
	{
		"forwarding-graph":
		{
			"id": "12345", 
			"name": "GraphName", 
			...
		}
	}
```

#### Delete a graph
```
	[DELETE]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```

#### Get the status of a graph
```
	[GET]
	Url: '/NF-FG/status/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```
Response:
```
	{
		"percentage_completed": 100,
		"status": "complete"
	}
```
