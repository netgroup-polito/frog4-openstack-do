# OpenStack Domain Orchestrator
This orchestrator controls an OpenStack domain. It is able to deploy service graphs according to the NF-FG used throghout the FROG4 architecture.
In addition to the creation of NFV service chains, it allows to steer traffic from an OpenStack port to another OpenStack port or to an external port and viceversa (e.g., a port that connects to the user located outside the OpenStack domain).
This result is achieved by interacting with the SDN controller which in turn has to be configured as the mechanism driver of the OpenStack's Neutron module. 

Currently, this domain orchestrator works with OpenStack Mitaka and Onos 1.9 as (optional) SDN controller. Support fo OpenDaylight is instead deprecated.

## REST API

This domain orchestrator offers a REST API which is shared among all the domain orchestrators of the FROG4 architecture.

REST interface provides several URL to authenticate, to send/get/delete a graph and to get the status of a graph. 

In order to discover which REST calls are supported you can see the API documentation at the URL `{Domain_Orchestrator_Address}/apidocs/index.html` once the domain orchestrator is installed and running.

## Documentation

The file [REAME_INSTALL.md](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_INSTALL.md) details how to set up the domain and execute the OpenStack domain orchestrator.

the file [README_LAUNCH_VNF.md](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_LAUNCH_VNF.md) shows instead how to deploy a VNF (as part of a service graph) in the OpenStack domain orchestrator.
