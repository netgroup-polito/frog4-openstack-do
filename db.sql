-- phpMyAdmin SQL Dump
-- version 4.5.4.1deb2ubuntu1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Creato il: Giu 30, 2016 alle 10:27
-- Versione del server: 5.7.12-0ubuntu1.1
-- Versione PHP: 7.0.4-7ubuntu2.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `openstack_orchestrator`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `action`
--

CREATE TABLE `action` (
  `id` int(64) NOT NULL,
  `flow_rule_id` varchar(64) NOT NULL,
  `output_type` varchar(64) DEFAULT NULL,
  `output` varchar(64) DEFAULT NULL,
  `controller` tinyint(1) DEFAULT NULL,
  `_drop` tinyint(1) NOT NULL,
  `set_vlan_id` varchar(64) DEFAULT NULL,
  `set_vlan_priority` varchar(64) DEFAULT NULL,
  `pop_vlan` tinyint(1) DEFAULT NULL,
  `set_ethernet_src_address` varchar(64) DEFAULT NULL,
  `set_ethernet_dst_address` varchar(64) DEFAULT NULL,
  `set_ip_src_address` varchar(64) DEFAULT NULL,
  `set_ip_dst_address` varchar(64) DEFAULT NULL,
  `set_ip_tos` varchar(64) DEFAULT NULL,
  `set_l4_src_port` varchar(64) DEFAULT NULL,
  `set_l4_dst_port` varchar(64) DEFAULT NULL,
  `output_to_queue` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `endpoint`
--

CREATE TABLE `endpoint` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(64) DEFAULT NULL,
  `graph_endpoint_id` varchar(64) NOT NULL,
  `graph_id` varchar(64) NOT NULL,
  `name` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `location` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `endpoint_resource`
--

CREATE TABLE `endpoint_resource` (
  `endpoint_id` int(64) NOT NULL,
  `resource_type` varchar(64) NOT NULL,
  `resource_id` int(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `flow_rule`
--

CREATE TABLE `flow_rule` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(255) DEFAULT NULL,
  `graph_flow_rule_id` varchar(64) NOT NULL,
  `graph_id` varchar(64) NOT NULL,
  `priority` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `node_id` varchar(64) DEFAULT NULL,
  `table_id` int(11) DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `graph`
--

CREATE TABLE `graph` (
  `id` int(64) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `node_id` varchar(64) DEFAULT NULL,
  `partial` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `match`
--

CREATE TABLE `match` (
  `id` int(64) NOT NULL,
  `flow_rule_id` varchar(64) NOT NULL,
  `port_in_type` varchar(64) DEFAULT NULL,
  `port_in` varchar(64) DEFAULT NULL,
  `ether_type` varchar(64) DEFAULT NULL,
  `vlan_id` varchar(64) DEFAULT NULL,
  `vlan_priority` varchar(64) DEFAULT NULL,
  `source_mac` varchar(64) DEFAULT NULL,
  `dest_mac` varchar(64) DEFAULT NULL,
  `source_ip` varchar(64) DEFAULT NULL,
  `dest_ip` varchar(64) DEFAULT NULL,
  `tos_bits` varchar(64) DEFAULT NULL,
  `source_port` varchar(64) DEFAULT NULL,
  `dest_port` varchar(64) DEFAULT NULL,
  `protocol` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `openstack_network`
--

CREATE TABLE `openstack_network` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `status` varchar(64) NOT NULL,
  `vlan_id` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `openstack_subnet`
--

CREATE TABLE `openstack_subnet` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `os_network_id` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `port`
--

CREATE TABLE `port` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(64) DEFAULT NULL,
  `graph_port_id` varchar(64) DEFAULT NULL,
  `graph_id` int(64) NOT NULL,
  `name` varchar(64) DEFAULT NULL,
  `vnf_id` varchar(64) DEFAULT NULL,
  `location` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `virtual_switch` varchar(64) DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  `os_network_id` varchar(64) DEFAULT NULL,
  `mac_address` varchar(64) DEFAULT NULL,
  `ipv4_address` varchar(64) DEFAULT NULL,
  `vlan_id` varchar(64) DEFAULT NULL,
  `local_ip` varchar(64) DEFAULT NULL,
  `remote_ip` varchar(64) DEFAULT NULL,
  `gre_key` varchar(64) DEFAULT NULL,
  `internal_group` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `session`
--

CREATE TABLE `session` (
  `id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `service_graph_id` varchar(63) NOT NULL,
  `service_graph_name` varchar(64) DEFAULT NULL,
  `status` varchar(64) NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `error` datetime DEFAULT NULL,
  `ended` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Struttura della tabella `tenant`
--

CREATE TABLE `tenant` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `description` varchar(128) CHARACTER SET utf8 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dump dei dati per la tabella `tenant`
--

INSERT INTO `tenant` (`id`, `name`, `description`) VALUES
('0', 'demo', 'Demo tenant'),
('1', 'PoliTO_chain1', 'openstack'),
('2', 'admin', 'Demo2 Tenant');

-- --------------------------------------------------------

--
-- Struttura della tabella `user`
--

CREATE TABLE `user` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `password` varchar(64) CHARACTER SET utf8 NOT NULL,
  `token` varchar(64) DEFAULT NULL,
  `token_timestamp` varchar(64) DEFAULT NULL,
  `tenant_id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `mail` varchar(64) CHARACTER SET utf8 DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dump dei dati per la tabella `user`
--

INSERT INTO `user` (`id`, `name`, `password`, `token`, `token_timestamp`, `tenant_id`, `mail`) VALUES
('0', 'demo', 'stack', NULL, NULL, '0', NULL),
('1', 'isp', 'stack', NULL, NULL, '1', NULL),
('2', 'admin', 'stackstack', 'abc', '1466673553', '2', NULL),
('3', 'AdminPoliTO', 'AdminPoliTO', 'abcdd', '1466673553', '1', NULL);

-- --------------------------------------------------------

--
-- Struttura della tabella `vnf_instance`
--

CREATE TABLE `vnf_instance` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(64) DEFAULT NULL,
  `graph_vnf_id` varchar(64) NOT NULL,
  `graph_id` int(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `template_location` varchar(64) DEFAULT NULL,
  `image_location` varchar(64) DEFAULT NULL,
  `location` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `last_update` datetime DEFAULT NULL,
  `availability_zone` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `action`
--
ALTER TABLE `action`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `endpoint`
--
ALTER TABLE `endpoint`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `endpoint_resource`
--
ALTER TABLE `endpoint_resource`
  ADD PRIMARY KEY (`endpoint_id`,`resource_type`,`resource_id`);

--
-- Indici per le tabelle `flow_rule`
--
ALTER TABLE `flow_rule`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `graph`
--
ALTER TABLE `graph`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `service_graph_id` (`session_id`,`node_id`);

--
-- Indici per le tabelle `match`
--
ALTER TABLE `match`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `openstack_network`
--
ALTER TABLE `openstack_network`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `openstack_subnet`
--
ALTER TABLE `openstack_subnet`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `port`
--
ALTER TABLE `port`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `graph_port_id` (`graph_port_id`,`vnf_id`);

--
-- Indici per le tabelle `session`
--
ALTER TABLE `session`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `tenant`
--
ALTER TABLE `tenant`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `vnf_instance`
--
ALTER TABLE `vnf_instance`
  ADD PRIMARY KEY (`id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
