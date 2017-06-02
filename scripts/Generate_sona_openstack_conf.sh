#!/bin/bash

echo -e "{\"apps\":{\"org.onosproject.openstacknode\" : {\"openstacknode\" : {\"nodes\" : [" | tee openstacknode_conf.json > /dev/null

if [[ -n $1 ]]; then

    ARGS=("$@")
    BRIDGE_ID[0]=""

#Generate Bridge ID
    COUNTER=1
    while [  $COUNTER -le $1 ]; do

        if [[ $COUNTER -ge 10 ]]; then

            BRIDGE_ID[$COUNTER]=of:000000000000a${COUNTER}

            let COUNTER=COUNTER+1

        else

            BRIDGE_ID[$COUNTER]=of:0000000000000a${COUNTER}

            let COUNTER=COUNTER+1

        fi

    done

# Generate JSON following the schema on config/openstacknode.json
    COUNTER=1
    INDEX=1
    while [  $COUNTER -le $1 ]; do

        echo -e "{\"hostname\" : \"compute-node"$COUNTER"\",\"type\" : \"COMPUTE\",\"managementIp\" : \""${ARGS[$INDEX]}"\",\"dataIp\" : \""${ARGS[$INDEX+1]}"\",\"integrationBridge\" : \""${BRIDGE_ID[$COUNTER]}"\"}" | tee -a openstacknode_conf.json > /dev/null

        let INDEX=INDEX+2
        let COUNTER=COUNTER+1

        if [[ $COUNTER -gt $1 ]]; then
            break
        else
            echo -e "," | tee -a openstacknode_conf.json > /dev/null
        fi
    done

    echo -e "]}}},\"devices\": {" | tee -a openstacknode_conf.json > /dev/null


    COUNTER=1
    while [  $COUNTER -le $1 ]; do

        echo -e "\""${BRIDGE_ID[$COUNTER]}"\" : { \"basic\" :{ \"driver\": \"sona\"}}" | tee -a openstacknode_conf.json > /dev/null

        let COUNTER=COUNTER+1

        if [[ $COUNTER -gt $1 ]]; then
            break
        else
            echo -e "," | tee -a openstacknode_conf.json > /dev/null
        fi
    done

    echo -e "}}" | tee -a openstacknode_conf.json > /dev/null

else
    echo "Usage: #compute_nodes [first_ip second_ip](for each compute node"
fi
