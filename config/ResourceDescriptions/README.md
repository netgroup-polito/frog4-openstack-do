This folder contains some examples of domain descriptions, written  according
to the [domain information library](https://github.com/netgroup-polito/domain-information-library).

The file `ResourceDescription.json` describes a domain with a single endpoint 
connected to an access network. Such an endpoint supports a single VLAN ID 
(i.e., 223), and does not support GRE tunnels. Moreover, the domain has the `
bridge` functional capability.

Instead, the file `ResourceDescription-with-neighbor.json` describes a domain 
in which the endpoint is connected to another domain (called `sdn_domain`).
