-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jul 18, 2017 at 08:40 PM
-- Server version: 5.5.55-0ubuntu0.14.04.1
-- PHP Version: 5.5.9-1ubuntu4.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `openstack_orchestrator`
--

-- --------------------------------------------------------

--
-- Table structure for table `action`
--

CREATE TABLE IF NOT EXISTS `action` (
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
  `output_to_queue` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `endpoint`
--

CREATE TABLE IF NOT EXISTS `endpoint` (
  `id` int(64) NOT NULL,
  `internal_id` varchar(64) DEFAULT NULL,
  `graph_endpoint_id` varchar(64) NOT NULL,
  `graph_id` varchar(64) NOT NULL,
  `name` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `location` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `endpoint_resource`
--

CREATE TABLE IF NOT EXISTS `endpoint_resource` (
  `endpoint_id` int(64) NOT NULL,
  `resource_type` varchar(64) NOT NULL,
  `resource_id` int(64) NOT NULL,
  PRIMARY KEY (`endpoint_id`,`resource_type`,`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `flow_rule`
--

CREATE TABLE IF NOT EXISTS `flow_rule` (
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
  `last_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `graph`
--

CREATE TABLE IF NOT EXISTS `graph` (
  `id` int(64) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `node_id` varchar(64) DEFAULT NULL,
  `partial` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `service_graph_id` (`session_id`,`node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `match`
--

CREATE TABLE IF NOT EXISTS `match` (
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
  `protocol` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `openstack_network`
--

CREATE TABLE IF NOT EXISTS `openstack_network` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `status` varchar(64) NOT NULL,
  `vlan_id` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `openstack_subnet`
--

CREATE TABLE IF NOT EXISTS `openstack_subnet` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `os_network_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `port`
--

CREATE TABLE IF NOT EXISTS `port` (
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
  `internal_group` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `graph_port_id` (`graph_port_id`,`vnf_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `session`
--

CREATE TABLE IF NOT EXISTS `session` (
  `id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `service_graph_id` varchar(63) NOT NULL,
  `service_graph_name` varchar(64) DEFAULT NULL,
  `status` varchar(64) NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `error` datetime DEFAULT NULL,
  `ended` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tenant`
--

CREATE TABLE IF NOT EXISTS `tenant` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `description` varchar(128) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `tenant`
--

INSERT INTO `tenant` (`id`, `name`, `description`) VALUES
('0', 'demo', 'Demo tenant'),
('1', 'PoliTO_chain1', 'openstack'),
('2', 'admin', 'admin_tenant');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE IF NOT EXISTS `user` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `password` varchar(64) CHARACTER SET utf8 NOT NULL,
  `token` varchar(64) DEFAULT NULL,
  `token_timestamp` varchar(64) DEFAULT NULL,
  `tenant_id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `mail` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `name`, `password`, `token`, `token_timestamp`, `tenant_id`, `mail`) VALUES
('0', 'demo', 'stack', NULL, NULL, '0', NULL),
('1', 'isp', 'stack', NULL, NULL, '1', NULL),
('2', 'admin', 'admin', NULL, NULL, '2', NULL),
('3', 'AdminPoliTO', 'AdminPoliTO', NULL, NULL, '1', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `vnf_instance`
--

CREATE TABLE IF NOT EXISTS `vnf_instance` (
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
  `availability_zone` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;