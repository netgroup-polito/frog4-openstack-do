# Install and configure ONOS (Open Network Operating System)
The installation instructions below have been tested on ubuntu 16.10.

### Required packages
First of all, you need to install some required Ubuntu packages. To do that, please just follow the steps below:
		
	sudo apt-get install python-pip
		
	sudo apt-get install software-properties-common -y && \
	sudo add-apt-repository ppa:webupd8team/java -y && \
	sudo apt-get update && \
	echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections && \
	sudo apt-get install oracle-java8-installer oracle-java8-set-default -y

### Install ONOS
Now we are able to install ONOS. We installed ONOS 1.8.4, choose your preferred ONOS version from here (http://downloads.onosproject.org).  
This are the steps to install it:  
`Note that later we'll use an URL path, within a configuration file, which is changed from "onos/openstackswitching" to "onos/openstacknetworking" since 1.8.0.`
		
	cd /opt
	sudo wget -c http://downloads.onosproject.org/release/onos-$ONOS_VERSION.tar.gz
	sudo tar xzf onos-$ONOS_VERSION.tar.gz
	sudo mv onos-$ONOS_VERSION onos
	sudo chown -R USERNAME:GROUP onos
`Substitute USERNAME and GROUP with your username and group so you don't have to run ONOS as root user. It's recommended to create an unprivileged user named sdn. To do this just type "sudo adduser sdn --system --group" and substitute USERNAME and GROUP with sdn respectively.`

Now you can run ONOS by typing in a terminal:
		
	cd /opt/onos/bin
	./onos-service start  
	
* `It's possible that ONOS will prompt a message saying JAVA_HOME is not set. To fix that problem shutdown ONOS typing within its CLI: system:shutdown,  
then follow the steps below:`  
	
		sudo gedit /etc/environment
		
		#Add this line at the end of the file:
		JAVA_HOME=/usr/lib/jvm/java-8-oracle
		
This path could be different if you use a different Java version. Now Restart Ubuntu to load the env variable.
#### Install ONOS Modular Layer 2 plug-in
As an additional step we need to install networking-onos, a Neutron ML2 plug-in for ONOS:
	
	cd
	git clone https://github.com/openstack/networking-onos.git
	cd networking-onos
	sudo python setup.py install

### Configure ONOS

* Follow all the steps listed within the [README_OPENSTACK.md](https://github.com/netgroup-polito/frog4-openstack-do/blob/onos-support/README_OPENSTACK.md) file, except those under "ML2 plugin configuration for ODL" section.
* When you reach that section, please follow this steps:  
 	* Configure the Modular Layer 2 (ML2) plug-in to use ONOS as a mechanism driver:  
	* Edit the /etc/neutron/plugins/ml2/ml2_conf.ini file and complete the following actions:
	
	    - In the [ml2] section set the following options: 
        
        		[ml2]
        		type_drivers = gre,vlan,vxlan
        		tenant_network_types = vxlan, gre
        		mechanism_drivers = onos_ml2
        		extension_drivers = port_security

        - In the [ml2_type_vxlan] section, configure the VXLAN network identifier range for networks:

        		[ml2_type_vxlan]
        		...
        		vni_ranges = 1:1000

        - In the [ml2_type_gre] section, configure the VXLAN network identifier range for networks:

        		[ml2_type_gre]
        		...
        		tunnel_id_ranges = 1:1000

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
* Now continue with the remaining steps within [README_OPENSTACK.md](https://github.com/netgroup-polito/frog4-openstack-do/blob/onos-support/README_OPENSTACK.md) file.
---
At the end check that ONOS is running all the required applications for communicating with Neutron:

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
	
	app activate org.onosproject.openstacknetworking
If some apps still missing, type those commands:
	
	feature:install <MISSING_APP>
	app activate <MISSING_APP>
