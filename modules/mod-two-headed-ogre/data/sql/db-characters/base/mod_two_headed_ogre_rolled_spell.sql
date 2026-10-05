-- mod-two-headed-ogre: spell roulette. Every level up gives the ogre a random class spell: even levels to
-- the body, odd levels to the head. The spell belongs to that head only (spellbook, casts).
CREATE TABLE IF NOT EXISTS `mod_two_headed_ogre_rolled_spell` (
    `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid of the ogre',
    `spell` INT UNSIGNED NOT NULL COMMENT 'first rank of the rolled spell chain',
    `owner` TINYINT UNSIGNED NOT NULL COMMENT '0 = body, 1 = head',
    `level` TINYINT UNSIGNED NOT NULL COMMENT 'level whose roll gave the spell',
    PRIMARY KEY (`guid`, `spell`),
    UNIQUE KEY `idx_level` (`guid`, `level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-two-headed-ogre spell roulette';
