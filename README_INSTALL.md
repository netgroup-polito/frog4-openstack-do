# FROG4 OpenStack Domain Orchestrator Installation Guide

The installation instructions below have been tested on ubuntu 16.04.

#### Required packages
First, you need to install all the required ubuntu packages. For this, please follow the steps below:
    
        sudo apt-get install python3-dev python3-setuptools python3-pip python3-sqlalchemy libmysqlclient-dev
		sudo pip3 install --upgrade falcon requests gunicorn jsonschema pymysql

#### Clone the code
Now you have to clone this repository _and_ all the submodules. Submodules include components that are part of the domain orchestrator but that are being developed in different repositories. This lead to the necessity to clone them as well in the right folders. For this, please follow the steps below:

        git clone https://github.com/netgroup-polito/frog4-openstack-do.git
        cd frog4-openstack-do
        git submodule init && git submodule update

#### DoubleDecker
The frog4-openstack-do uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker) messaging system to communicate with the other components of the FROG4 architecture. In order to launch the frog4-openstack-do you need to install DoubleDecker.
	
		$ git clone https://github.com/Acreo/DoubleDecker
		$ cd DobuleDecker/python/
Now you can follow the instruction provided in that folder. You can choose to install it in your system or simply copy the doubledecker folder in the [do_core](do_core) folder with the following command:

		cp -R doubledecker/ {domain_orchestrator_root}/do_core/
In this way the frog4-openstack-do will use the DoubleDecker sources in his folder, otherwise it will use the installed version, if present.

#### Modify the configuration parameters
For this, you need to modify the [config/default-config.ini](config/default-config.ini) file according to your preferences.

#### Create database
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
        
#### Run the domain orchestrator
You can launch this domain orchestrator by executing the following script in the domain orchestrator root folder, optionally specifying the configuration file (example: conf/config.ini):
        
        python3 gunicorn.py [--d conf-file]

#### Useful scripts
You can find some helpful scripts inside the [scripts](scripts) folder. For example, if you need to clean all sessions and graphs currently stored in the database, you can launch the following script in the domain orchestrator root folder:
        
        python3 -m scripts.clean_db_sessions
