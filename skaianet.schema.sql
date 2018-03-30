-- MySQL dump 10.15  Distrib 10.0.33-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: skaianet
-- ------------------------------------------------------
-- Server version	10.0.33-MariaDB-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `administrators`
--

DROP TABLE IF EXISTS `administrators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `administrators` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL,
  `password` varchar(64) NOT NULL COMMENT 'sha256 checksum of password',
  `level` int(11) NOT NULL COMMENT '(unused?)',
  `resetpw` tinyint(1) NOT NULL COMMENT 'prompt for password WITHOUT AUTHENTICATION next time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_2` (`id`),
  KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `library`
--

DROP TABLE IF EXISTS `library`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `library` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(511) NOT NULL COMMENT 'Song title',
  `artist` varchar(127) NOT NULL COMMENT 'Song performer',
  `album` varchar(127) NOT NULL COMMENT 'album name',
  `filepath` varchar(255) NOT NULL COMMENT 'absolute path on disk (for use by ices to feed icecast)',
  `albumart` varchar(255) DEFAULT NULL COMMENT 'URL for listener to fetch display art (this is per-song not per-album)',
  `autoplay` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'ices will only add these songs if no request is made',
  `requestable` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'songs that can appear in the oh.php interface',
  `mdchanged` tinyint(1) NOT NULL DEFAULT '0' COMMENT '(unknown)',
  `length` int(11) DEFAULT NULL COMMENT 'song duration (in seconds)',
  `website` varchar(255) DEFAULT NULL COMMENT 'URL for a listener to click if they wish to learn more about the song/artist (ie. bandcamp link)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `filepath_UNIQUE` (`filepath`),
  KEY `i_autoplay` (`autoplay`)
) ENGINE=InnoDB AUTO_INCREMENT=1980 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `most_recent`
--

DROP TABLE IF EXISTS `most_recent`;
/*!50001 DROP VIEW IF EXISTS `most_recent`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `most_recent` (
  `id` tinyint NOT NULL,
  `songid` tinyint NOT NULL,
  `title` tinyint NOT NULL,
  `artist` tinyint NOT NULL,
  `album` tinyint NOT NULL,
  `length` tinyint NOT NULL,
  `reqname` tinyint NOT NULL,
  `reqsrc` tinyint NOT NULL,
  `time` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `random_fresh_song`
--

DROP TABLE IF EXISTS `random_fresh_song`;
/*!50001 DROP VIEW IF EXISTS `random_fresh_song`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `random_fresh_song` (
  `id` tinyint NOT NULL,
  `title` tinyint NOT NULL,
  `artist` tinyint NOT NULL,
  `album` tinyint NOT NULL,
  `filepath` tinyint NOT NULL,
  `albumart` tinyint NOT NULL,
  `autoplay` tinyint NOT NULL,
  `requestable` tinyint NOT NULL,
  `mdchanged` tinyint NOT NULL,
  `length` tinyint NOT NULL,
  `website` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `recent`
--

DROP TABLE IF EXISTS `recent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `recent` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `songid` int(11) NOT NULL,
  `title` varchar(1024) NOT NULL,
  `artist` varchar(1024) NOT NULL,
  `album` varchar(1024) NOT NULL,
  `length` int(11) NOT NULL,
  `reqname` varchar(1024) NOT NULL,
  `reqsrc` varchar(1024) NOT NULL,
  `time` datetime NOT NULL,
  `listeners` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `i_time` (`time`),
  KEY `i_songid` (`songid`)
) ENGINE=InnoDB AUTO_INCREMENT=533325 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `requests`
--

DROP TABLE IF EXISTS `requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reqid` int(11) NOT NULL,
  `reqname` varchar(1024) NOT NULL DEFAULT 'Anonymous' COMMENT 'Who asked',
  `reqsrc` varchar(1024) NOT NULL COMMENT 'library.id requested',
  `override` tinyint(1) NOT NULL DEFAULT '0' COMMENT '(unknown)',
  PRIMARY KEY (`id`),
  KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `commercialrate` int(11) NOT NULL,
  `repeatcheckrate` int(11) NOT NULL,
  `notifytype` int(11) NOT NULL,
  `notifytext` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `v_recent_max_time`
--

DROP TABLE IF EXISTS `v_recent_max_time`;
/*!50001 DROP VIEW IF EXISTS `v_recent_max_time`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `v_recent_max_time` (
  `songid` tinyint NOT NULL,
  `time` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `most_recent`
--

/*!50001 DROP TABLE IF EXISTS `most_recent`*/;
/*!50001 DROP VIEW IF EXISTS `most_recent`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `most_recent` AS select `r1`.`id` AS `id`,`r1`.`songid` AS `songid`,`r1`.`title` AS `title`,`r1`.`artist` AS `artist`,`r1`.`album` AS `album`,`r1`.`length` AS `length`,`r1`.`reqname` AS `reqname`,`r1`.`reqsrc` AS `reqsrc`,`r1`.`time` AS `time` from (`recent` `r1` join `v_recent_max_time` `r2` on(((`r1`.`songid` = `r2`.`songid`) and (`r1`.`time` = `r2`.`time`)))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `random_fresh_song`
--

/*!50001 DROP TABLE IF EXISTS `random_fresh_song`*/;
/*!50001 DROP VIEW IF EXISTS `random_fresh_song`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `random_fresh_song` AS (select `library`.`id` AS `id`,`library`.`title` AS `title`,`library`.`artist` AS `artist`,`library`.`album` AS `album`,`library`.`filepath` AS `filepath`,`library`.`albumart` AS `albumart`,`library`.`autoplay` AS `autoplay`,`library`.`requestable` AS `requestable`,`library`.`mdchanged` AS `mdchanged`,`library`.`length` AS `length`,`library`.`website` AS `website` from `library` where ((`library`.`autoplay` = 1) and (not(`library`.`id` in (select `recent`.`songid` from `recent` where (`recent`.`time` > (now() - interval 1 hour)))))) order by rand() limit 1) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_recent_max_time`
--

/*!50001 DROP TABLE IF EXISTS `v_recent_max_time`*/;
/*!50001 DROP VIEW IF EXISTS `v_recent_max_time`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_recent_max_time` AS select `recent`.`songid` AS `songid`,max(`recent`.`time`) AS `time` from `recent` group by `recent`.`songid` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-03-26  3:46:33
