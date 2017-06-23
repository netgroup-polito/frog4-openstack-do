# FROG4 OpenStack Domain Orchestrator Installation Guide

The installation instructions below have been tested on ubuntu 16.04.

## OpenStack and ONOS

To install OpenStack and the ONOS SDN controller, please follows the instructions provided respectively in [README_OPENSTACK](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_OPENSTACK.md) and in [README_ONOS](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_ONOS.md).
Note that ONOS is optional but highly recommended.

## Required packages
First, you need to install all the required ubuntu packages. For this, please follow the steps below:
    
        $ sudo apt-get install python3-dev python3-setuptools python3-pip python3-sqlalchemy libmysqlclient-dev        
        $ sudo pip3 install --upgrade requests gunicorn jsonschema pymysql flask flasgger

## Clone the code
Now you have to clone this repository _and_ all the submodules. Submodules include components that are part of the domain orchestrator but that are being developed in different repositories. This lead to the necessity to clone them as well in the right folders. For this, please follow the steps below:

        $ git clone https://github.com/netgroup-polito/frog4-openstack-do.git
        $ cd frog4-openstack-do
        $ git submodule init && git submodule update

## Install the DoubleDecker client

The SDN domain orchestrator uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker-py) messaging system to communicate with the FROG4-orchestrators. Then, you need to install the DoubleDecker client.

		$ git clone https://github.com/Acreo/DoubleDecker-py.git		
		$ cd DoubleDecker-py
		$ git reset --hard dc556c7eb30e4c90a66e2e00a70dfb8833b2a652
		$ cp -r [frog4-sdn-do]/patches .
		$ git am patches/doubledecker_client_python/0001-version-protocol-rollbacked-to-v3.patch
		
Now you can install the DubleDeker as follows:

		#install dependencies 
		$ sudo apt-get update
		$ sudo apt-get install python3-setuptools python3-nacl python3-zmq python3-urwid python3-tornado
		# install the doubledecker module and scripts
		$ sudo python3 setup.py install

## OpenStack domain orchestrator configuration file
For this, you need to modify the [config/default-config.ini](config/default-config.ini) file according to your preferences and your configuration. 
It is very important to correctly set the templates section, in order to retrieve templates in a local directory or by means of a [VNF-Repository] (https://github.com/netgroup-polito/VNF-repository).
This guide assumes OpenStack and the SDN controller already installed and correctly configured. For general guidelines refer to the [README_OPENSTACK](README_OPENSTACK.md) file.

## Create the SQL database
The FROG4 OpenStack Domain Orchestrator uses a local mySQL database that has to be created and initialized by executing the steps below.

- Create database and user for OpenStack orchestrator database:
	    
        mysql -u root -p
        mysql> CREATE DATABASE openstack_orchestrator;
        mysql> GRANT ALL PRIVILEGES ON openstack_orchestrator.* TO 'orchestrator'@'localhost' IDENTIFIED BY 'ORCH_DBPASS';
        mysql> GRANT ALL PRIVILEGES ON openstack_orchestrator.* TO 'orchestrator'@'%' IDENTIFIED BY 'ORCH_DBPASS';	
        mysql> exit;
    
- Create tables in the domain orchestrator db (all the initialization parameters are stored in the ``db.sql`` file):
    
        mysql -u orchestrator -p -Dopenstack_orchestrator < db.sql

- Change the the parameters used to connect to the database in the configuration file:

        [db]
        # Mysql DB
        connection = mysql+pymysql://orchestrator:ORCH_DBPASS@127.0.0.1/openstack_orchestrator

On the last OpenStack version username and tenantnane must be the same to avoid authentication error
        
# Run the domain orchestrator
You can launch this domain orchestrator by executing the following script in the domain orchestrator root folder, optionally specifying the configuration file (example: conf/config.ini):
        
        ./start_orchestrator.sh [--d conf-file]

# Useful scripts
You can find some helpful scripts inside the [scripts](scripts) folder. For example, if you need to clean all sessions and graphs currently stored in the database, you can launch the following script in the domain orchestrator root folder:
        
        python3 -m scripts.clean_db_sessions
# ONOS support
In order to use ONOS as network controller for the Openstack-do, you have to install the OVSDB-rest application. Just follow the guide at this link: https://github.com/netgroup-polito/onos-applications/tree/master/ovsdb-rest
* Remember to update the ovsdb-rest consifguration based on your topology (usually an ovsdb node for each compute node)
* If you followed the README of this repo to install onos, remember to clone the ONOS git at https://github.com/opennetworkinglab/onos in your home folder, and to type ". onos/tools/dev/bash_profile". This enable some useful onos scripts, like onos-app, used to install ovsdb-rest app. That's because the guide uses a non developer ONOS version.
