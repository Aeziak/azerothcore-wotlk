-- mod-two-headed-ogre v2: one ogre character shared by two accounts.
-- The core table `character_shared_access` lets the second account log into the character;
-- this table keeps the two head names and which account plays which head.
CREATE TABLE IF NOT EXISTS `mod_two_headed_ogre_pair` (
    `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid of the ogre',
    `head1_name` VARCHAR(12) NOT NULL COMMENT 'first head, also the character name',
    `head1_account` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 = free head',
    `head2_name` VARCHAR(12) NOT NULL COMMENT 'second head',
    `head2_account` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 = free head, waiting for a partner',
    PRIMARY KEY (`guid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-two-headed-ogre heads';
