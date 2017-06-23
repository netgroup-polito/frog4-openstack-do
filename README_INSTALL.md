# FROG4 OpenStack Domain Orchestrator Installation Guide

The installation instructions below have been tested on ubuntu 16.04.

## OpenStack and ONOS

To install OpenStack and the ONOS SDN controller, please follows the instructions provided respectively in [README_OPENSTACK](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_OPENSTACK.md) and in [README_ONOS](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_ONOS.md).
Note that ONOS is optional but highly recommended.

## Required packages
First, you need to install all the required ubuntu packages. For this, please follow the steps below:
    
        $ sudo apt-get install python3-dev python3-setuptools python3-pip python3-sqlalchemy libmysqlclient-dev git   
        $ sudo pip3 install --upgrade requests gunicorn jsonschema pymysql flask flasgger

## Clone the code
Now you have to clone this repository _and_ all the submodules. Submodules include components that are part of the domain orchestrator but that are being developed in different repositories. This lead to the necessity to clone them as well in the right folders. For this, please follow the steps below:

        $ git clone https://github.com/netgroup-polito/frog4-openstack-do.git
        $ cd frog4-openstack-do
        $ git submodule init && git submodule update
	
## ONOS support

In order to use ONOS as network controller for the Openstack domain, you have to install the [ovsdb-rest](https://github.com/netgroup-polito/onos-applications/tree/master/ovsdb-rest) application. Just follow the [guide](https://github.com/netgroup-polito/onos-applications/blob/master/ovsdb-rest/README.md) in that repository.

* Remember to update the ovsdb-rest consifguration based on your topology (usually an ovsdb node for each compute node)
* If you followed the [README_ONOS.md](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_ONOS.md) to install ONOS, remember to clone the ONOS git at https://github.com/opennetworkinglab/onos in your home folder, and to type `. onos/tools/dev/bash_profile`. This enables some useful onos scripts, like `onos-app`, used to install ovsdb-rest app. That is because the guide uses a non developer ONOS version.

## Install the DoubleDecker client

The SDN domain orchestrator uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker-py) messaging system to communicate with the FROG4-orchestrators. Then, you need to install the DoubleDecker client.

		$ git clone https://github.com/Acreo/DoubleDecker-py.git		
		$ cd DoubleDecker-py
		$ git reset --hard dc556c7eb30e4c90a66e2e00a70dfb8833b2a652
		$ cp -r [frog4-os-do]/patches .
		$ git am patches/doubledecker_client_python/0001-version-protocol-rollbacked-to-v3.patch
		
Now you can install the DubleDeker as follows:

		#install dependencies 
		$ sudo apt-get update
		$ sudo apt-get install python3-setuptools python3-nacl python3-zmq python3-urwid python3-tornado
		# install the doubledecker module and scripts
		$ sudo python3 setup.py install
		
## Create the SQL database
The FROG4 OpenStack Domain Orchestrator uses a local mySQL database that has to be created and initialized by executing the steps below.

- Create database and user for OpenStack orchestrator database:
	    
        mysql -u root -p
        mysql> CREATE DATABASE openstack_orchestrator;
        mysql> GRANT ALL PRIVILEGES ON openstack_orchestrator.* TO 'orchestrator-user'@'localhost' IDENTIFIED BY 'orchestrator-pwd';
        mysql> GRANT ALL PRIVILEGES ON openstack_orchestrator.* TO 'orchestrator-user'@'%' IDENTIFIED BY 'rchestrator-pwd';	
        mysql> exit;
    
    where `orchestrator-user` and orchestrator-pwd can be replaced respectively by the username and the password that the FROG4-orchestator will use to access to the SQL database.
    
- Create tables in the domain orchestrator db (all the initialization parameters are stored in the ``db.sql`` file):
    
        mysql -u orchestrator-user -p -Dopenstack_orchestrator < db.sql
	
When it asks the password, enter that used above (i.e., `orchestrator-pwd)`. The process may take some seconds.

The script above also adds in the database the `admin` user (`username:admin`, `password:admin`, `tenant:admin_tenant`).

- Change the the parameters used to connect to the database in the configuration file:

        [db]
        # Mysql DB
        connection = mysql+pymysql://orchestrator:ORCH_DBPASS@127.0.0.1/openstack_orchestrator

On the last OpenStack version username and tenantnane must be the same to avoid authentication error

### Create a new user

TODO

## OpenStack domain orchestrator configuration file

Edit [./default-config.ini](/config/default-config.ini) following the instructions that you find inside the file itself.
The most important fields that you have to consider are described in the following.

In the section `[openstack_orchestrator]`, set the field `port` to the TCP port to be used to interact with the OpenStack domain orchestrator through its REST API.

In this section, you must also configure the IP address of your OpenStack installation (`openstack_ip` field).

In the [config](/config/) folder, make a new copy of the file `ResourceDescription.json` and rename it (e.g. `ResourceDescription.json`). Then, in the [configuration file](/config/default-config.ini) section `[domain_description]`, change the path in the `file` field so that it points to the new file (e.g. `file = configMyResourceDescription.json`).

In the section `[doubledecker]`, you have to configure the connection towards the broker (note that this guide supposes that, if you need a broker, you have already installed it). Particularly, you can set the URL to be used to contact such a module (`broker_address`) and the file containing the key to be used (`dd_keyfile`).

In the section `[templates]`, in case the NFs templates are stored in the Datastore, you have to set the field `source = vnf-repository`, while the field `epository_ur` must contain the URL to be used to contact the datastore itself.

If you are using ONOS as SDN controller, edit the section `[onos]` with the proper information. Instead, if you are using OpenDaylight, edit the `[odl]` section.

In the `[db]` section, you have to edit the `connection` parameter so that it includes the `orchestrator-user` and `orchestrator-pwd` chosen before when configuring the SQL database.

### JOLNET considerations

If you are going to execute the OpenStack domain orchestrator on the JOLNET, set to true the parameter `jolnet_mode` in the section `[jolnet]`. In this section, you must also edit the parameter `jolnet_networks`, so that it contains the OpenStack networks to be used.

Finally, in the `[openstack_orchestrator]` section, you have to set the field `identity_api_version` to `2`. 


# Adding the WEB GUI on top of the SDN domain orchestrator

It is possible to configure the [FROG4 GUI](https://github.com/netgroup-polito/fg-gui), so that it can be used to interact with the SDN domain orchestrator (e.g., to deploye new service graphs, or to read the service graphs currently deployed).
To install the GUI, follows the [instructions](https://github.com/netgroup-polito/fg-gui/blob/master/README_INSTALL.md) provided with the repository.
        
# Run the domain orchestrator
You can launch this domain orchestrator by executing the following script in the domain orchestrator root folder, optionally specifying the configuration file (example: [conf/config.ini](conf/config.ini)):
        
        ./start_orchestrator.sh [--d conf-file]

# Useful scripts
You can find some helpful scripts inside the [scripts](scripts) folder. For example, if you need to clean all sessions and graphs currently stored in the database, you can launch the following script in the domain orchestrator root folder:
        
        python3 -m scripts.clean_db_sessions
