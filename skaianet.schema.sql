-- MariaDB dump 10.19  Distrib 10.6.12-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: skaianet
-- ------------------------------------------------------
-- Server version	10.6.12-MariaDB-0ubuntu0.22.04.1

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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `library`
--

DROP TABLE IF EXISTS `library`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `library` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(191) NOT NULL COMMENT 'Song title',
  `artist` varchar(191) NOT NULL COMMENT 'Song performer',
  `album` varchar(191) NOT NULL COMMENT 'album name',
  `filepath` varchar(191) NOT NULL COMMENT 'absolute path on disk (for use by ices to feed icecast)',
  `albumart` varchar(191) DEFAULT NULL COMMENT 'URL for listener to fetch display art (this is per-song not per-album)',
  `autoplay` tinyint(1) NOT NULL DEFAULT 1 COMMENT 'ices will only add these songs if no request is made',
  `requestable` tinyint(1) NOT NULL DEFAULT 1 COMMENT 'songs that can appear in the oh.php interface',
  `length` int(11) DEFAULT NULL COMMENT 'song duration (in seconds)',
  `website` varchar(191) DEFAULT NULL COMMENT 'URL for a listener to click if they wish to learn more about the song/artist (ie. bandcamp link)',
  `last_played` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `filepath_UNIQUE` (`filepath`),
  KEY `i_autoplay` (`autoplay`)
) ENGINE=InnoDB AUTO_INCREMENT=2141 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `most_recent`
--

DROP TABLE IF EXISTS `most_recent`;
/*!50001 DROP VIEW IF EXISTS `most_recent`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `most_recent` AS SELECT
 1 AS `recentid`,
  1 AS `songid`,
  1 AS `title`,
  1 AS `artist`,
  1 AS `album`,
  1 AS `length`,
  1 AS `reqname`,
  1 AS `reqsrc`,
  1 AS `time` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `random_christmas_song`
--

DROP TABLE IF EXISTS `random_christmas_song`;
/*!50001 DROP VIEW IF EXISTS `random_christmas_song`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `random_christmas_song` AS SELECT
 1 AS `id`,
  1 AS `title`,
  1 AS `artist`,
  1 AS `album`,
  1 AS `filepath`,
  1 AS `albumart`,
  1 AS `autoplay`,
  1 AS `requestable`,
  1 AS `length`,
  1 AS `website`,
  1 AS `last_played` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `random_fresh_song`
--

DROP TABLE IF EXISTS `random_fresh_song`;
/*!50001 DROP VIEW IF EXISTS `random_fresh_song`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `random_fresh_song` AS SELECT
 1 AS `id`,
  1 AS `title`,
  1 AS `artist`,
  1 AS `album`,
  1 AS `filepath`,
  1 AS `albumart`,
  1 AS `autoplay`,
  1 AS `requestable`,
  1 AS `length`,
  1 AS `website`,
  1 AS `last_played` */;
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
) ENGINE=InnoDB AUTO_INCREMENT=1448233 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
  `override` tinyint(1) NOT NULL DEFAULT 0 COMMENT '(unknown)',
  PRIMARY KEY (`id`),
  KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3851 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
  `notifytext` mediumtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `v_recent_max_time`
--

DROP TABLE IF EXISTS `v_recent_max_time`;
/*!50001 DROP VIEW IF EXISTS `v_recent_max_time`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `v_recent_max_time` AS SELECT
 1 AS `songid`,
  1 AS `time` */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `most_recent`
--

/*!50001 DROP VIEW IF EXISTS `most_recent`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `most_recent` AS select `r1`.`id` AS `recentid`,`r1`.`songid` AS `songid`,`r1`.`title` AS `title`,`r1`.`artist` AS `artist`,`r1`.`album` AS `album`,`r1`.`length` AS `length`,`r1`.`reqname` AS `reqname`,`r1`.`reqsrc` AS `reqsrc`,`r1`.`time` AS `time` from (`recent` `r1` join `v_recent_max_time` `r2` on(`r1`.`songid` = `r2`.`songid` and `r1`.`time` = `r2`.`time`)) order by `r1`.`time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `random_christmas_song`
--

/*!50001 DROP VIEW IF EXISTS `random_christmas_song`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `random_christmas_song` AS select `library`.`id` AS `id`,`library`.`title` AS `title`,`library`.`artist` AS `artist`,`library`.`album` AS `album`,`library`.`filepath` AS `filepath`,`library`.`albumart` AS `albumart`,`library`.`autoplay` AS `autoplay`,`library`.`requestable` AS `requestable`,`library`.`length` AS `length`,`library`.`website` AS `website`,`library`.`last_played` AS `last_played` from `library` where `library`.`autoplay` = 1 and (`library`.`album` = 'Homestuck for the Holidays' or `library`.`title` like '%hristmas%') order by rand() limit 1 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `random_fresh_song`
--

/*!50001 DROP VIEW IF EXISTS `random_fresh_song`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `random_fresh_song` AS select `subquery`.`id` AS `id`,`subquery`.`title` AS `title`,`subquery`.`artist` AS `artist`,`subquery`.`album` AS `album`,`subquery`.`filepath` AS `filepath`,`subquery`.`albumart` AS `albumart`,`subquery`.`autoplay` AS `autoplay`,`subquery`.`requestable` AS `requestable`,`subquery`.`length` AS `length`,`subquery`.`website` AS `website`,`subquery`.`last_played` AS `last_played` from (select `library`.`id` AS `id`,`library`.`title` AS `title`,`library`.`artist` AS `artist`,`library`.`album` AS `album`,`library`.`filepath` AS `filepath`,`library`.`albumart` AS `albumart`,`library`.`autoplay` AS `autoplay`,`library`.`requestable` AS `requestable`,`library`.`length` AS `length`,`library`.`website` AS `website`,`library`.`last_played` AS `last_played` from `library` where `library`.`autoplay` = 1 order by rand() limit 20) `subquery` order by `subquery`.`last_played` limit 1 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_recent_max_time`
--

/*!50001 DROP VIEW IF EXISTS `v_recent_max_time`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
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

-- Dump completed on 2023-05-07  6:42:46
