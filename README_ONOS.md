# Install and configure ONOS (Open Network Operating System)
The installation instructions below have been tested on ubuntu 16.10.

## Preliminaries

This README assumes that you have already deployed [OpenStack](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_OPENSTACK.md). 

In case you have deployed it through devstack, you have to execute the following commands before continuing with the installation of ONOS:

	$ sudo ovs-vsctl del-br br-int
	$ sudo ovs-vsctl del-br br-ex

## Required packages
First of all, you need to install some required Ubuntu packages. To do that, please just follow the steps below:
				
	$ sudo apt-get install software-properties-common -y 
	$ sudo add-apt-repository ppa:webupd8team/java -y 
	$ sudo apt-get update 
	$ echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections 
	$ sudo apt-get install oracle-java8-installer oracle-java8-set-default -y

## Install ONOS
Now we are able to install ONOS. In this guide we install ONOS 1.8.4; other versiona can be downloaded from [here](http://downloads.onosproject.org).  

Before, we create an unprivileged user named `sdn`:

	$ sudo adduser sdn --system --group
	
This are the steps to install it:  
`Note that later we will use an URL path, within a configuration file, which is changed from "onos/openstackswitching" to "onos/openstacknetworking" since 1.8.0.`
		
	$ cd /opt
	$ export ONOS_VERSION=1.8.4
	$ sudo wget -c http://downloads.onosproject.org/release/onos-$ONOS_VERSION.tar.gz
	$ sudo tar xzf onos-$ONOS_VERSION.tar.gz
	$ sudo mv onos-$ONOS_VERSION onos
	$ sudo chown -R sdn:sdn onos
	
Now you can run ONOS by typing in a terminal:
		
	$ cd /opt/onos/bin
	$ ./onos-service start  
	
It is possible that ONOS prompts a message saying *JAVA_HOME is not set*. 
To fix that problem, shutdown as follows

	onos> system:shutdown
	
In case you are using Java 8, type the following commands: 

	$ sudo nano /etc/environment

	#Add this line at the end of the file:
	JAVA_HOME=/usr/lib/jvm/java-8-oracle
		
To know the version of Java, use the command

	$ file /etc/alternatives/java /etc/alternatives/javac

Now restart the machine to load the environment variable, and start again ONOS.

After this procedure, ONOS can be reached through its REST API at the URL: `127.0.0.1:8181/onos/ui` . The username is `onos`, the password is `rocks`.

## Install ONOS Modular Layer 2 plug-in
As an additional step we need to install networking-onos, a Neutron ML2 plug-in for ONOS:
	
	$ cd
	$ git clone https://github.com/openstack/networking-onos.git
	$ cd networking-onos
	$ sudo python setup.py install

## Configure ONOS

### Configuring the OpenStack Modular Layer 2 plug-in

The Modular Layer 2 (ML2) plug-in in OpenStack must be configured to use ONOS as a mechanism driver:  

* Edit the /etc/neutron/plugins/ml2/ml2_conf.ini file and complete the following actions:
	
	    - In the [ml2] section set the following options: 
        
        		[ml2]
        		type_drivers = vxlan
        		tenant_network_types = vxlan
        		mechanism_drivers = onos_ml2
        		extension_drivers = port_security

        - In the [ml2_type_vxlan] section, configure the VXLAN network identifier range for networks:

        		[ml2_type_vxlan]
        		...
        		vni_ranges = 1:1000

        - In the [securitygroup] section, set the following options:

        		[securitygroup]
        		...
        		firewall_driver = neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver
                	enable_ipset = True

        - Add the [onos] section with the following options:
            - Replace ONOS_IP with the proper values.

        		[onos]
        		url_path = http://ONOS_IP:8181/onos/openstacknetworking
        		username = onos
        		password = rocks
`Remeber that since  ONOS 1.8.0 version the url_path is changed from "onos/openstackswitching" to "onos/openstacknetworking"`

### Testing the ONOS setup

Check that ONOS is running all the required applications for communicating with Neutron:

	onos> apps -s -a
	*   8 org.onosproject.optical-model        1.8.4    Optical information model
	*  16 org.onosproject.ovsdb-base           1.8.4    OVSDB Provider
	*  17 org.onosproject.drivers.ovsdb        1.8.4    OVSDB Device Drivers
	*  18 org.onosproject.openstacknode        1.8.4    OpenStack Node Bootstrap App
	*  21 org.onosproject.openstackinterface   1.8.4    OpenStack Interface App
	*  22 org.onosproject.dhcp                 1.8.4    DHCP Server App
	*  23 org.onosproject.openstackswitching   1.8.4    OpenStack Switching App
	*  35 org.onosproject.openflow-base        1.8.4    OpenFlow Provider
	*  42 org.onosproject.scalablegateway      1.8.4    Scalable GW App
	*  43 org.onosproject.openstackrouting     1.8.4    OpenStack Routing App
	*  76 org.onosproject.drivers              1.8.4    Default device drivers
	*  82 org.onosproject.openstacknetworking  1.8.4    OpenStack Networking App
	
If not, type this command within ONOS CLI:
	
	app activate org.onosproject.drivers.ovsdb
	app activate org.onosproject.ovsdb-base
	app activate org.onosproject.openstacknetworking
	app activate org.onosproject.openflow-base
If some apps still missing, type those commands:
	
	feature:install <MISSING_APP>
	app activate <MISSING_APP>

### Sona Configuration

* **SONA(Simplified Overlay Network Architecture)**, basically, it's a set of ONOS applications which provides OpenStack Neutron ML2 mechanism driver and L3 service plugin. In the current ONOS version (1.10), SONA is composed of three ONOS applications: *openstackNode*, *openstackNetworking*, and *vRoute*r. We used ONOS 1.9 so SONA includes also *openstackInterface*, substituted later in version 1.10 by third parts library. SONA supports only VXLAN type driver, so the network is seen as a big switch where each ovS in the compute node is part of that, all of them connected through VXLAN
* **OpenstackNode** application is in charge of managing and bootstrapping compute and gateway nodes. In our case will have only compute nodes, so the connectivity of the various network through a router is not available.
* **OpenstackNetworking** application is in charge of managing virtual network states and providing a network connectivity to virtual machines by setting flow rules to compute and gateway node's OvS. This application also expose REST API, previously configure in neutron conf file, which are called by networking-onos. So OpenstackNetworking handle East-West traffic in each compute node(remember that North-South traffic is not handled).
* Each application has its own configuration file, an example for each app is provided within config folder.
---
Now we have to configure OpenstackInterface and OpenstackNode applications. Once you have a running ONOS instance with all the required apps running, you can configure SONA.
First of all write your configuration files. In the OpenstackNode config file add all of your compute nodes, assigning a different id to each integration bridge. Also update "devices" section with all the integration bridge, one for each compute node.

About OpenstackInterface's config file, unfortunately it uses the old v2 keystone and neutron api. So you have to make ONOS able to authenticate through keystone:

Type this command to retrieve the domain id:

	openstack domain list
	
Then add the domain id within /etc/keystone/keystone.conf like this:

	[identity] 
	
	default_domain_id  = YOUR_DOMAIN_ID

Then run keystone DB sync:

	$ sudo su
	# /bin/sh -c "keystone-manage --config-file /etc/keystone/keystone.conf db_sync" keystone
	
The last step is to configure ovs in each compute node to listen on port 6640, because after posting the configuration files, OpenstackNode apps will connect to OVSDB at each node and then will create an integration bridge setting your ONOS instance as Openflow controller:

		$ sudo ovs-appctl -t ovsdb-server ovsdb-server/add-remote ptcp:6640:[compute_node_ip]
	        $ sudo ovs-vsctl set-manager ptcp:6640
		
Finally add the two configuration files:

	curl --user onos:rocks -X POST -H "Content-Type: application/json" http://ONOS_IP_:8181/onos/v1/network/configuration/ -d @OpenstackInterface.json
	curl --user onos:rocks -X POST -H "Content-Type: application/json" http://ONOS_IP_:8181/onos/v1/network/configuration/ -d @OpenstackNode.json


Now you should see on OVS at each compute node, an integration bridge with a VXLAN port setted. Run

	$ sudo ovs-vsctl show
	
to check the configuration.
