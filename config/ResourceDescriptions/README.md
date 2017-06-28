This folder contains some examples of domain descriptions, written  according
to the [domain information library](https://github.com/netgroup-polito/domain-information-library).

The file [ResourceDescription.json](ResourceDescription.json) describes a domain with a single endpoint 
connected to an access network. Such an endpoint supports a single VLAN ID 
(i.e., 223), and does not support GRE tunnels. Moreover, the domain has the `
bridge` functional capability.

The file [ResourceDescription-with-neighbor-vlan.json](ResourceDescription-with-neighbor-vlan.json) describes a domain 
in which the endpoint is connected to another domain (called `sdn_domain`).
Also in this case, the VLAN ID 223 can be used for the inter-domain traffic 
steering.

The file [ResourceDescription-with-neighbor-gre.json](ResourceDescription-with-neighbor-gre.json) describes a domain 
in which the endpoint is connected to another domain (called `openstack_domain-two`).
In this case, GRE tunnels can be used for the inter-domain traffic steering.
It is worth noting that, due to current limitation of our formalism, the interface name must be in the form `ip_address/interface_name`. 
