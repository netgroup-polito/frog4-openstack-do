# How to launch a Virtual Network Function (VNF) in the OpenStack domain

This document details how to deploy and run a Virtual Network Function (VNF) in the OpenStack domain. This requires the execution of the following main steps (detailed in the remainder of the document):

* Upload the VNF image in the OpenStack Glance component;
* Write the [VNF template](https://github.com/netgroup-polito/vnf-template-library) and upload it in the [FROG4 Datastore](https://github.com/netgroup-polito/frog4-datastore);
* In the ResourceDescription file exported by the OpenStack domain orchestrator, specify that the domain supports the functional capability implemented by the VNF;
* Write your NF-FG that uses the VNF.

## Upload the VNF image

Your VNF image must be uploaded in the OpenStack Glance component. Then Glance assigns your image with an ID, which can be retrieve from the OpenStack Horizon dashboard:

* Logs in in Horizon;
* On the right, click on the `Images` tab;
* From here, you can find your image in the `Project` tab and/or in the `Public` tab;
* Click on the VNF image name in order to open a tab containing several information about the image. Among the others, you can find the **ID**

## Write the VNF template

The VNF template describes several aspects of the VNF, and must be written according to the [VNF template library](https://github.com/netgroup-polito/vnf-template-library). 

As example is the following:

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

Ad example is the following (not that the information about interfaces are omitted for the sake of clarity):

{  
  "netgroup-domain:informations": {  
    "id": "001",  
    "capabilities": {  
      "infrastructural-capabilities": {  
        "infrastructural-capability": [  
          {  
            "name": "x86-64",  
            "type": "cpu_architecture"  
          },  
          {  
            "name": "openstack",  
            "type": "compute_controller"  
          }  
        ]  
      },  
      "functional-capabilities": {  
        "functional-capability": [  
          {  
            "ready": "true",  
            "name": "my beatiful bridge",  
            "family": "Network",  
            "function-specifications": {  
              "function-specification": []  
            },  
            "type": "bridge"  
          }  
        ]  
      }  
    },  
    "hardware-informations": {  
      "interfaces": {  
		...  
      }  
    },  
    "name": "openstack",  
    "management-address": "192.168.0.100:9200",  
    "type": "OS"  
  }  
}  

The most important parameters are the following:

* `management-address`: the URL to be used to interact with the OpenStack domain orchestrator;
* `type`: indicates the domain type, which is `OS` (i.e., OpenStack) in our case;
* `functional-capability`-`type`: the functional capability associated with your VNF. In our example, our VNF image implements a `bridge`.

## Write and deploy your NF-FG

The NF-FG must be written according to the [NF-FG library](https://github.com/netgroup-polito/nffg-library).

An example of graph using our VNF is the following:

{
  "forwarding-graph": {
    "id": "123",
    "name": "Demo Graph 1",
    "VNFs": [
      {
        "id": "00000001",
        "name": "client",
        "vnf_template":"IU9LBT",
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
        "vlan": {
          "node-id": "of:000034dbfd3c1140",
          "vlan-id": "297",
          "if-name": "5097"
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

In the description of the VNF, the most important parameters are:

* `vnf_template`: this must correspond to the VNF ID returned by the Datastore when the VNF template have been uploaded. In our example, it is `IU9LBT`;
* `functional-capability`: it must correspond to the functional capability implemented by the desired VNF, `bridge` in our use case.

You can deploy the NF-FG above through the [deploy_graph.py script](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/scripts/deploy_graph.py). This graph can then be deleted through the [delete_graph.py script](https://github.com/netgroup-polito/frog4-openstack-do/blob/master/scripts/delete_graph.py).

