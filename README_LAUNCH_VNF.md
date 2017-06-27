# How to launch a Virtual Network Function (VNF) in the OpenStack domain

This document details how to deploy and run a Virtual Network Function (VNF) in the OpenStack domain. This requires the execution of the following main steps (detailed in the remainder of the document):

* Upload the VNF image in the OpenStack Glance component;
* Write the [VNF template](https://github.com/netgroup-polito/vnf-template-library) and upload it in the [FROG4 Datastore](https://github.com/netgroup-polito/frog4-datastore);
* In the ResourceDescription file exported by the OpenStack domain orchestrator, specify that the domain supports the functional capability implemented by the VNF;
* Write your [NF-FG](https://github.com/netgroup-polito/nffg-library) that uses the VNF.

## Upload the VNF image

Your VNF image must be uploaded in the OpenStack Glance component. Then Glance assigns your image with an ID, which can be retrieve from the OpenStack Horizon dashboard:

* Logs in in Horizon;
* On the right, click on the `Images` tab;
* From here, you can find your image in the `Project` tab and/or in the `Public` tab;
* Click on the VNF image name in order to open a tab containing several information about the image. Among the others, you can find the **ID**

## Write the VNF template

The VNF template describes several aspects of the VNF, and must be written according to the [VNF template library](https://github.com/netgroup-polito/vnf-template-library). 

As example is the following:

```json
{  
  "CPUrequirements": {  
    "platformType": "x86",  
    "socket": [  
      {  
        "coreNumbers": 1  
      }  
    ]  
  },  
  "memory-size": 512,  
  "name": "my beatiful bridge",  
  "functional-capability": "bridge",  
  "ephemeral-file-system-size": 0,  
  "vnf-type": "virtual-machine-kvm",  
  "uri": "http://10.0.0.1:9292/v2/images/dfb458f9-e618-4901-8dc4-ee3eaa80349c",  
  "swap-disk-size": 0,  
  "uri-type": "remote-file",  
  "expandable": false,  
  "ports": [  
    {  
      "name": "eth",  
      "min": "1",  
      "label": "inout",  
      "ipv4-config": "none",  
      "position": "0-N",  
      "ipv6-config": "none"  
    }  
  ],  
  "root-file-system-size": 1  
}  
```

The most important parameters are the following:

* `vnf-type`: indicates the technology to be used to execxute the VNF. In the example, it is a KVM virtual machine;
* `functional-capability`: indicates the functional capability associated with the VNF. In the example, our VNF implements a bridge;
* `uri`: this is the URI to be used to retrieve the VNF image. It corresponds to a URI in the OpenStack Glance component. Notably, the last part of the URI (`dfb458f9-e618-4901-8dc4-ee3eaa80349c` in our example) is the ID assigned by Glance to the VNF image. This ID can be retrieve as described above.

## Upload the VNF template in the Datastore

The VNF template must be uploaded in the [FROG4 datastore](https://github.com/netgroup-polito/frog4-datastore). 
This can be done through the [FROG4 GUI](https://github.com/netgroup-polito/frog4-gui):

* Logs in in the GUI; 
* Click on `NF Repository` on the right;
* Press on the `+` icon;
* Select, from your local file system, the template to be uploaded;
* Press on the box in order to say that your VNF image is not on the Datastore (in fact, we have uploaded in the OpenStack Glance component);
* Click on `Add NF`.

At this point you will get the VNF ID to be used in the NF-FG to be deployed in the OpenStack domain.

## Edit the ResourceDescription file

In the [ResourceDescription](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/README_INSTALL.md#openstack-domain-description) file you must specify that the domain is able to implement the functional capability associated with your VNF, e.g., `bridge` in our example.
Note that this file must be written according to the [domain information library](https://github.com/netgroup-polito/domain-information-library). 

Ad example is the following (not that the information about interfaces are omitted for the sake of clarity):

```json
{
  "netgroup-domain:informations": {
    "id": "00000001",
    "name": "openstack_domain",
    "type": "OS",
    "management-address": "130.192.225.106:9200",
    "hardware-informations": {
      "":""
    },    
    "capabilities": {
      "infrastructural-capabilities": {
        "infrastructural-capability": [
          {
            "type": "cpu_architecture",
            "name": "x86-64"
          },
           {
            "type": "compute_controller",
            "name": "openstack"
          }
        ]
      },
      "functional-capabilities": {
        "functional-capability": [
          {
            "type": "bridge",
            "name": "bridge",
            "ready": true,
            "template": "bridge-template.json",
            "family": "Network",
            "function-specifications": {
              "function-specification": []
            }
          }
        ]
      }
    }
  }
}

```

The most important parameters are the following:

* `management-address`: the URL to be used to interact with the OpenStack domain orchestrator;
* `type`: indicates the domain type, which is `OS` (i.e., OpenStack) in our case;
* `functional-capability`-`type`: the functional capability associated with your VNF. In our example, our VNF image implements a `bridge`.

## Write and deploy your NF-FG

The NF-FG must be written according to the [NF-FG library](https://github.com/netgroup-polito/nffg-library).

An example of graph using our VNF is the following:

```json
{  
  "forwarding-graph": {  
    "id": "123",  
    "name": "my graph",  
    "VNFs": [  
      {  
        "id": "00000001",  
        "name": "bridge",  
        "vnf_template":"JJT643",  
        "functional-capability":"bridge",  
        "ports": [  
          {  
            "id": "inout:0"  
          }  
        ]  
      }  
    ],  
    "end-points": [  
      {  
        "type": "vlan",  
        "domain": "openstack_domain",  
        "vlan": {  
          "node-id": "openstack_domain",  
          "vlan-id": "282",  
          "if-name": "of:000028c7ce9f66040/5104"  
        },  
        "id": "00000001"  
      }  
    ],  
    "big-switch": {  
      "flow-rules": [  
        {  
          "match": {  
            "port_in": "vnf:00000001:inout:0"  
          },  
          "actions": [  
            {  
              "output_to_port": "endpoint:00000001"  
            }  
          ],  
          "priority": 40001,  
          "id": "1"  
        },  
        {  
          "match": {  
            "port_in": "endpoint:00000001"  
          },  
          "actions": [  
            {  
              "output_to_port": "vnf:00000001:inout:0"  
            }  
          ],  
          "priority": 40001,  
          "id": "2"  
        }  
      ]  
    }  
  }  
}  
```

In the description of the VNF, the most important parameters are:

* `vnf_template`: this must correspond to the VNF ID returned by the Datastore when the VNF template has been uploaded. In our example, it is `IU9LBT`;
* `functional-capability`: it must correspond to the functional capability implemented by the desired VNF, `bridge` in our use case.
**WARNING** due to a bug, currently the `functional-capability` and the VNF `name` should be set to the same value.

You can deploy the NF-FG above through the [deploy_graph.py script](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/scripts/deploy_graph.py):

        $ cd [frog4-os-do]/scripts
        $ python3 deploy_graph.py
	
Before running the script, edit it with your credential that must be used for the authentication in the OpenStack domain orchestrator, and set the proper VNF ID returned by the Datastore when the VNF template has been uploaded.
Note that you can also deploy other graphs, by properly editing the script.

After running the script, you can check that your VNF is running through the OpenStack Horizon dashboard:
* Logs in in Horizon;
* On the right, click on the `Instances` tab.

From the `Network` -> `Network Topology` tab, you can instad check that your VM is connected to one of the OpenStack networks, as required by the NF-FG.

This graph can then be deleted through the [delete_graph.py script](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/scripts/delete_graph.py):


        $ cd [frog4-os-do]/scripts
        $ python3 delete_graph.py
	
Before running the script, edit it with your credential that must be used for the authentication in the OpenStack domain orchestrator.

