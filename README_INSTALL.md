# FROG4 OpenStack Domain Orchestrator Installation Guide

The instructions below have been tested on ubuntu 16.04.

## OpenStack and ONOS

To install OpenStack and the ONOS SDN controller, please follows the instructions provided respectively in [README_OPENSTACK](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_OPENSTACK.md) and in [README_ONOS](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_ONOS.md).
Note that ONOS is optional but highly recommended.

## Required packages
First, you need to install all the required ubuntu packages. For this, please follow the steps below:
    
        $ sudo apt-get install python3-dev python3-setuptools python3-pip python3-sqlalchemy libmysqlclient-dev mysql-server git   
        $ sudo pip3 install --upgrade requests gunicorn jsonschema pymysql flask flask-restplus Flask-SQLAlchemy

## Clone the code
Now you have to clone this repository _and_ all the submodules. Submodules include components that are part of the domain orchestrator but that are being developed in different repositories. This lead to the necessity to clone them as well in the right folders. For this, please follow the steps below:

        $ git clone https://github.com/netgroup-polito/frog4-openstack-do.git
        $ cd frog4-openstack-do
        $ git submodule init && git submodule update
	
## ONOS support

In order to use ONOS as network controller for the Openstack domain, you have to install the [ovsdb-rest](https://github.com/netgroup-polito/onos-applications/tree/master/ovsdb-rest) application in the SDN controller. 
To this purpose, follow the [guide](https://github.com/netgroup-polito/onos-applications/blob/master/ovsdb-rest/README.md) in that repository.

* Remember to update the ovsdb-rest configuration. In the guide mentioned above, it's described a configuration file. Edit the file based on  your environment, i.e. leave the port as it is (6640) and update the ovsdbIp with the IP address of your compute node. If you have more than one compute node, add an entry (ovsdbIP + ovsdbPort) within the nodes array in the config file, one for each compute node.
* Within the guide mentioned above, it's described the installation process of the ovsdb-rest app using the "onos-app" command. This command usually is not available, so you have to clone the ONOS git at https://github.com/opennetworkinglab/onos in your home folder:

		git clone https://github.com/opennetworkinglab/onos 

and type `. onos/tools/dev/bash_profile`. This enables some useful onos scripts, like `onos-app`, used to install ovsdb-rest app.

## Install the DoubleDecker client

The SDN domain orchestrator uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker-py) messaging system to communicate with the FROG4-orchestrators. Then, you need to install the DoubleDecker client.

		$ git clone https://github.com/Acreo/DoubleDecker-py.git		
		$ cd DoubleDecker-py
		$ git reset --hard dc556c7eb30e4c90a66e2e00a70dfb8833b2a652
		$ cp -r [frog4-os-do]/patches .
		$ git am patches/doubledecker_client_python/0001-version-protocol-rollbacked-to-v3.patch
		
Now you can install DoubleDecker as follows:

		; install dependencies 
		$ sudo apt-get update
		$ sudo apt-get install python3-setuptools python3-nacl python3-zmq python3-urwid python3-tornado
		; install the doubledecker module and scripts
		$ sudo python3 setup.py install
		
## Create the SQL database
The FROG4 OpenStack Domain Orchestrator uses a local mySQL database that has to be created and initialized by executing the steps below.

- Create database and user for OpenStack orchestrator database:
	    
        mysql -u root -p
        mysql> CREATE DATABASE openstack_orchestrator;
        mysql> GRANT ALL PRIVILEGES ON openstack_orchestrator.* TO 'orch-user'@'localhost' IDENTIFIED BY 'orch-pwd';
        mysql> GRANT ALL PRIVILEGES ON openstack_orchestrator.* TO 'orch-user'@'%' IDENTIFIED BY 'orch-pwd';	
        mysql> exit;
    
    where `orch-user` and `orch-pwd` can be replaced respectively by the username and the password that the FROG4-orchestator will use to access to the SQL database.
    
- Create tables in the domain orchestrator db (all the initialization parameters are stored in the ``db.sql`` file):
    
        $ cd [frog4-os-do]
        $ mysql -u orch-user -p -Dopenstack_orchestrator < db.sql
	
When it asks the password, enter that used above (i.e., `orch-pwd)`. The process may take some seconds.

The script above also adds in the database the `admin` user (`username:admin`, `password:admin`, `tenant:admin_tenant`).

### Create a new user

To create a new user, run:

    $ cd [frog4-os-do]
    $ python3 -m scripts.create_user


**IMPORTANT**
In order to work, the OpenStack domain orchestrator requires that the database contains the same user (in terms of username, password and tenant) that is stored in the *Keystone* OpenStack module.

Moreover, in the last OpenStack releases, `username` and `tenantnane` must be the same to avoid authentication error.

## OpenStack domain description

The file [ResourceDescription.json](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/config/ResourceDescription.json) contains the description of the domain, both from the *networking* (e.g., information about boundary interfaces) and *computing* (i.e., functional capabilities) points of view.

It is written according to the [domain information library](https://github.com/netgroup-polito/domain-information-library).

You have to edit this file so that it actually decribes the domain under the responsibility of the OpenStack domain orchestrator. 

**IMPORTANT** Please, note that the functional capabilties must be written manually and must correspond to those available in the [Datastore](https://github.com/netgroup-polito/frog4-datastore/blob/master/README.md) used by the OpenStack domain orchestrator.

## OpenStack domain orchestrator configuration file

Edit [./default-config.ini](/config/default-config.ini) following the instructions that you find inside the file itself.
The most important fields that you have to consider are described in the following.

In the section `[openstack_orchestrator]`, set the field `port` to the TCP port to be used to interact with the OpenStack domain orchestrator through its REST API.
Moreover, in this section you must configure the `availability_zone`, to select the OpenStack availability zone that the Domain Orchestrator have to use to deploy the network functions.
If you do not specify the availability zone, this will be selected by the OpenStack Nova component.
Finally, in the `[openstack_orchestrator]` section you must also configure the IP address of your OpenStack installation (`openstack_ip` field).

In the [config/ResourceDescriptions](/config/ResourceDescriptions) folder, make a new copy of the file `ResourceDescription.json` and rename it (e.g. `MyResourceDescription.json`). Then, in the [configuration file](/config/default-config.ini) section `[domain_description]`, change the path in the `file` field so that it points to the new file (e.g. `file = config/MyResourceDescription.json`).

In the section `[doubledecker]`, you have to configure the connection towards the broker (note that this guide supposes that, if you need a broker, you have already installed it). Particularly, you can set the URL to be used to contact such a module (`broker_address`) and the file containing the key to be used (`dd_keyfile`).

In the section `[templates]`, in case the NFs templates are stored in the Datastore, you have to set the field `source = datastore`, while the field `datastore_url` must contain the URL to be used to contact the datastore itself.

If you are using ONOS as SDN controller, edit the section `[onos]` with the proper information. Instead, if you are using OpenDaylight, edit the `[odl]` section.

In the `[db]` section, you have to edit the `connection` parameter so that it includes the `orch-user` and `orch-pwd` chosen before when configuring the SQL database.

### JOLNET considerations

If you are going to execute the OpenStack domain orchestrator on the JOLNET, set to true the parameter `jolnet_mode` in the section `[jolnet]`. In this section, you must also edit the parameter `jolnet_networks`, so that it contains the OpenStack networks to be used.

In addition, in the `[openstack_orchestrator]` section, you have to set the field `identity_api_version` to `2`. 

Please, note that the JOLNET does not use any SDN controller in the OpenStack domain, then you have to edit neither the `[onos]`, nor the `[odl]` sections.

# The FROG 4 datastore

The [Datastore](https://github.com/netgroup-polito/frog4-datastore/) can be used by the OpenStack domain orchestrator to retrieve the VNF templates. To install this component, follow the instructions provided in the [Datastore repository](https://github.com/netgroup-polito/frog4-datastore/blob/master/README.md).

# Adding the WEB GUI on top of the OpenStack domain orchestrator

It is possible to configure the [FROG4 GUI](https://github.com/netgroup-polito/fg-gui), so that it can be used to interact with the SDN domain orchestrator (e.g., to deploye new service graphs, or to read the service graphs currently deployed).
To install the GUI, follows the [instructions](https://github.com/netgroup-polito/fg-gui/blob/master/README_INSTALL.md) provided with the repository.
        
# Run the domain orchestrator
You can launch this domain orchestrator as follows, optionally specifying the configuration file (example: [conf/config.ini](conf/config.ini)):
        
        cd [frog4-openstack-do]
        $ ./start_orchestrator.sh [-d conf-file]

# Useful scripts
You can find some helpful scripts inside the [scripts](scripts) folder. For example, if you need to clean all sessions and graphs currently stored in the database, you can launch the following script in the domain orchestrator root folder:
        
        python3 -m scripts.clean_db_sessions
