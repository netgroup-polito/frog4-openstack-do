This folder contains some config file and Forwarding Graph example.

The [default-config.ini](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/default-config.ini) file describes the default configuration for the Domain Orchestrator. The role of each field within that file is described in the file itself.

The [openstackInterface.json](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/openstackInterface.json) file is used by SONA to be able to interact with the various Openstack submodules. This file is used only with ONOS <= 1.9.0 as pointed in the relative [guide](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_ONOS.md) within the Sona Configuration section.

The [openstacknode.json](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/openstacknode.json) file is an example of the SONA configuration file pointed in this [guide](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_ONOS.md). In this example the file describes a domain made up of two compute nodes. This file can be generated using this [script](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/scripts/Generate_sona_openstack_conf.sh)

The [ovsdbrest.json](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/ovsdbrest.json) file is an example of configuration requested by the Ovsdb-rest app. More information can be found [here](https://github.com/netgroup-polito/onos-applications/tree/master/ovsdb-rest).

The [firstGraph.json](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/firstGraph.json) file describes a FG that connects two VNFs togheter.

The [SecondGraph.json](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/SecondGraph.json) file describes a FG that connects an endpoint with a VNF.

The [ResourceDescriptions](https://github.com/netgroup-polito/frog4-openstack-do/tree/master/config/ResourceDescriptions) folder contains some examples of domain descriptions, written according to the [domain information library](https://github.com/netgroup-polito/domain-information-library).
