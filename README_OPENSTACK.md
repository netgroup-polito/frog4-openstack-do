# OpenStack brief installation guide
The installation guide has been tested with Ubuntu 14.04, OpenStack Mitaka and OpenDaylight Beryllium.

## Vanilla OpenStack (stable/mitaka version):

During the development phase we leveraged the official guide (http://docs.openstack.org/mitaka/install-guide-ubuntu/) for the installation and the configuration of components of interest.
Design your OpenStack network and configure it according to your needs.

The component that have to be installed are the following:

* Identity service (keystone)
* Image service (glance)
* Compute service (nova)
* Networking service (neutron)
* Dashboard GUI (horizon)
		
Extras: we suggest also to install phpmyadmin on controller node, to get database operations easier

You can follow the official guide to install all these components except for the Networking service whose instructions are presented below. Therefore this is a partial guide and we assume that you have already installed all the required services.

## Configure OpenDaylight
We recommend to install OpenDaylight on a separate VM with at least 2 core and 2GB of memory and to place it on the controller node. Of course you can also install it as a separate server, in case you don't care about saving space. Furthermore you can also install OpenDaylight directly on the controller node if you cannot deploy it in a fresh Ubuntu.

Download OpenDaylight Beryllium (https://www.opendaylight.org/software/downloads/beryllium-sr2) and follow the installation guide (https://www.opendaylight.org/introduction-getting-started-guide) in order to install and run it.

The only feature you need to install on the first run of ODL is "odl-ovsdb-openstack" and, then,  it is ready to be used as a Neutron ML2 plugin.

## Networking service installation on the controller node

Here are the steps required to install and configure the Neutron module on a OpenStack Mitaka controller node.

- Create a database, service credentials, and API endpoints:
    - Create the dataase needed by Neutron:
        - Replace the NEUTRON_DBPASS with a password of your choice.
        
                mysql -u root -p
                CREATE DATABASE neutron;
                GRANT ALL PRIVILEGES ON neutron.* TO 'neutron'@'localhost' IDENTIFIED BY 'NEUTRON_DBPASS';
                GRANT ALL PRIVILEGES ON neutron.* TO 'neutron'@'%' IDENTIFIED BY 'NEUTRON_DBPASS';

    - Source the admin credentials to gain access to admin-only CLI commands (you should have created this file during the installation of the Identity service):

            . admin-openrc

    - Create the neutron user and add the admin role to it:
        - We will refer to the password chosen for the neutron user as NEUTRON_PASS
        
        		openstack user create --domain default --password-prompt neutron
        		openstack role add --project service --user neutron admin

    - Create the neutron service entity:

            openstack service create --name neutron  --description "OpenStack Networking" network

    - Create the Networking service API endpoints:

    		openstack endpoint create --region RegionOne network public http://controller:9696
    		openstack endpoint create --region RegionOne network internal http://controller:9696
    		openstack endpoint create --region RegionOne network admin http://controller:9696

    - Install the required packages:

            sudo apt-get install neutron-server neutron-plugin-ml2 neutron-l3-agent neutron-dhcp-agent neutron-metadata-agent python-networking-odl

- Configure the Neutron service:

    - Edit the /etc/neutron/neutron.conf file and complete the following actions:
        - In the [database] section, configure database access:

            	[database]
            	...
            	connection = mysql+pymysql://neutron:NEUTRON_DBPASS@controller/neutron
            	Replace NEUTRON_DBPASS with the password you chose for the database.

        - In the [DEFAULT] section, enable the Modular Layer 2 (ML2) plug-in, router service, and overlapping IP addresses:

            	[DEFAULT]
            	...
            	core_plugin = ml2
            	service_plugins = router
            	allow_overlapping_ips = True

        - In the [DEFAULT] and [oslo_messaging_rabbit] sections, configure RabbitMQ message queue access:
            - Replace RABBIT_PASS with the password you chose for the openstack account in RabbitMQ.

            		[DEFAULT]
            		...
            		rpc_backend = rabbit
            
            		[oslo_messaging_rabbit]
            		...
            		rabbit_host = controller
            		rabbit_userid = openstack
            		rabbit_password = RABBIT_PASS


        - In the [DEFAULT] and [keystone_authtoken] sections, configure Identity service access:
            - Replace NEUTRON_PASS with the password you chose for the neutron user in the Identity service. Comment out or remove any other options in the [keystone_authtoken] section.
        		
            		[DEFAULT]
            		...
            		auth_strategy = keystone
            
            		[keystone_authtoken]
            		...
            		auth_uri = http://controller:5000
            		auth_url = http://controller:35357
            		memcached_servers = controller:11211
            		auth_type = password
            		project_domain_name = default
            		user_domain_name = default
            		project_name = service
            		username = neutron
            		password = NEUTRON_PASS

        - In the [DEFAULT] and [nova] sections, configure Networking to notify Compute of network topology changes:
            - Replace NOVA_PASS with the password you chose for the nova user in the Identity service.

            		[DEFAULT]
            		...
            		notify_nova_on_port_status_changes = True
            		notify_nova_on_port_data_changes = True
            
            		[nova]
            		...
            		auth_url = http://controller:35357
            		auth_type = password
            		project_domain_name = default
            		user_domain_name = default
            		region_name = RegionOne
            		project_name = service
            		username = nova
            		password = NOVA_PASS


- Configure the Modular Layer 2 (ML2) plug-in to use OpenDaylight as a mechanism driver:
    - Edit the /etc/neutron/plugins/ml2/ml2_conf.ini file and complete the following actions:
        - In the [ml2] section set the following options: 
        
        		[ml2]
        		type_drivers = gre,vlan,vxlan
        		tenant_network_types = vxlan, gre
        		mechanism_drivers = opendaylight
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

        - Add the [ml2_odl] section with the following options:
            - Replace ODL_USER, ODL_PASS and ODL_IP with the proper values.

            		[ml2_odl]
            		username = ODL_USER
            		password = ODL_PASS
            		url = http://ODL_IP:8080/controller/nb/v2/neutron


- Configure the layer-3 agent:
    - Edit the /etc/neutron/l3_agent.ini file and complete the following actions:
        - In the [DEFAULT] section paste the following rows:

        		[DEFAULT]
        		...
        		interface_driver = neutron.agent.linux.interface.OVSInterfaceDriver
        		external_network_bridge =


- Configure the DHCP agent:
    - Edit the /etc/neutron/dhcp_agent.ini file and complete the following actions:
        - In the [DEFAULT] section, paste the following values:

        		[DEFAULT]
        		...
        		interface_driver = neutron.agent.linux.interface.OVSInterfaceDriver
        		dhcp_driver = neutron.agent.linux.dhcp.Dnsmasq
        		enable_isolated_metadata = True
        		
- Configure the metadata agent:
    - Edit the /etc/neutron/metadata_agent.ini file and complete the following actions:
        - In the [DEFAULT] section, configure the metadata host and shared secret:
            - Replace METADATA_SECRET with a suitable secret for the metadata proxy.

            		[DEFAULT]
            		...
            		nova_metadata_ip = controller
            		metadata_proxy_shared_secret = METADATA_SECRET
            		
- Configure Compute to use Networking:
    - Edit the /etc/nova/nova.conf file and perform the following actions:
        - In the [neutron] section, configure access parameters, enable the metadata proxy, and configure the secret:
            - Replace NEUTRON_PASS with the password you chose for the neutron user in the Identity service.
            - Replace METADATA_SECRET with the secret you chose for the metadata proxy.
            
            		[neutron]
            		...
            		url = http://controller:9696
            		auth_url = http://controller:35357
            		auth_type = password
            		project_domain_name = default
            		user_domain_name = default
            		region_name = RegionOne
            		project_name = service
            		username = neutron
            		password = NEUTRON_PASS
            
            		service_metadata_proxy = True
            		metadata_proxy_shared_secret = METADATA_SECRET
		

- Finalize the installation:

		su -s /bin/sh -c "neutron-db-manage --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head" neutron

- Restart services:

		service nova-api restart
		service neutron-server restart
		service neutron-dhcp-agent restart
		service neutron-l3-agent restart
		service neutron-metadata-agent restart


## Networking service installation on the compute node

Here are the steps required to install and configure the Neutron module on a OpenStack Mitaka compute node.

- Install the required package:
        
        sudo apt-get install neutron-common

- Configure the Networking common components (the Networking common component configuration includes the authentication mechanism, message broker, and plug-in):
    
    - Configure Networking to use the Identity service for authentication:
        - Edit the /etc/neutron/neutron.conf file and add the following key to the [DEFAULT] section:

                [DEFAULT]
                ...
                auth_strategy = keystone
    
    - Add the following keys to the [keystone_authtoken] section:
        - Replace NEUTRON_PASS with the passwords used in the controller installation.

                [keystone_authtoken]
                ...
                auth_uri = http://controller:5000
                auth_uri = http://controller:35357
                memcached_servers = controller:11211
                auth_type = password
                project_domain_name = default
                user_domain_name = default
                project_name = service
                username = neutron
                password = NEUTRON_PASS

    - Configure Networking to use the message broker:
        - Edit the /etc/neutron/neutron.conf file and add the following keys to the [DEFAULT] section:
            - Replace RABBIT_PASS with the passwords used in the controller installation.
        
                    [DEFAULT]
                    ...
                    rpc_backend = rabbit
            
                    [oslo_messaging_rabbit]
                    ...
                    rabbit_host = controller
                    rabbit_userid = openstack
                    rabbit_password = RABBIT_PASS
                    
    - Configure Networking to use the Modular Layer 2 (ML2) plug-in:
        - Edit the /etc/neutron/neutron.conf file and add the following key to the [DEFAULT] section:

                [DEFAULT]
                ...
                core_plugin = ml2
 

- Configure Compute to use Networking. By default, most distributions configure Compute to use legacy networking. You must reconfigure Compute to manage networks through Networking. 
    
    - Edit the /etc/nova/nova.conf and add the following keys to the [DEFAULT] section:
        - Replace NEUTRON_PASS with the password used in the controller installation.

                [neutron]
                ...
                url = http://controller:9696
                auth_url = http://controller:35357
                auth_type = password
                project_domain_name = default
                user_domain_name = default
                region_name = RegionOne
                project_name = service
                username = neutron
                password = NEUTRON_PASS

- Finalize the installation, restart the Compute service:

        sudo service nova-compute restart


## Install Openvswitch (controller and compute node)
The following operations have to be performed on the controller and on the compute node.

- Stop the Neutron server (on controller node only)
        
        service neutron-server stop
        
- Install the package:

		sudo apt-get install openvswitch-switch

- Retrieve the Openvswitch ID:
    -  The code in the first line of the output of the command is the OVS_ID.
            
            sudo ovs-vsctl show
- WARNING: Now perform the following commands ONLY if you plan to use Opendaylight as network controller rather than ONOS:

  - Replace OVS_ID with the Openvswitch ID just retrieved, IP with the IP address of the local machine and ODL_IP with the IP address of the OpenDaylight controller.

		sudo ovs-vsctl set Open_vSwitch OVS_ID other_config={local_ip=IP}
		sudo ovs-vsctl set-manager tcp:<ODL_IP>:6640

- Restart the neutron server (on controller node only):

        service neutron-server start


### Prototype configuration (compute node only)

#### WARNING: Now perform the following commands ONLY if you plan to use Opendaylight as network controller rather than ONOS (because ONOS will take care of this operations based on your graph. Example: gre-endpoint on the br-ex):

- Configure the external bridge

    - Add an L2 bridge that manage the exit traffic (it is necessary to deliver the traffic coming from the internet to the NF-FG graph of the correct user, which happens when multiple users are connected to your compute node):

            sudo ovs-vsctl add-br br-ex

    - Add a physical network interface, connected to the Internet, to the external bridge, so the traffic of all NF-FGs will exit through that interface:

        - Replace INTERFACE_NAME with the actual interface name. For example, eth0 or em0
            
                sudo ovs-vsctl add-port br-ex INTERFACE_NAME
            
        WARNING: at this point, if you were connected to the node through the interface you had bridged to br-ex, you are no longer able to reach the node. If it is possible, you should use two different interfaces: one for management and the other for the outgoing traffic of NF-FGs. 
        
        If no additional interface are available, to restore the connection you should perform the following steps in order to assign the IP address to the bridge:
        - Remove the IP address from the interface

                sudo ifconfig INTERFACE_NAME 0 

        - Configure the interface and the bridge in /etc/network/interfaces
    
                auto INTERFACE_NAME
                iface INTERFACE_NAME inet manual
                auto br-ex
                iface br-ex inet dhcp

        - Restart the configuration of br-ex:

                sudo ifdown br-ex
                sudo ifup br-ex

        - Remove the controller from br-ex (this is a bridge that does not need to be controlled by OpenDaylight):

                sudo ovs-vsctl del-controller br-ex
