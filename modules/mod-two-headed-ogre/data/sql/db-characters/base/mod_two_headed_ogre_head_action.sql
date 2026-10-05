-- mod-two-headed-ogre: action bars of the head (co-pilot client). The body uses the character's own
-- bars (character_action); the head's bars are kept here, per ogre and per account.
CREATE TABLE IF NOT EXISTS `mod_two_headed_ogre_head_action` (
    `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid of the ogre',
    `account` INT UNSIGNED NOT NULL COMMENT 'account playing the head',
    `button` TINYINT UNSIGNED NOT NULL,
    `data` INT UNSIGNED NOT NULL COMMENT 'packed action (low 24 bits) and type (high 8 bits)',
    PRIMARY KEY (`guid`, `account`, `button`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-two-headed-ogre head action bars';
