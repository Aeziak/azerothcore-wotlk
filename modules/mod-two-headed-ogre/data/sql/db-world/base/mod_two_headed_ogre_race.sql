-- mod-two-headed-ogre v2: the Ogre playable race (race 9, the unused Goblin slot), Horde.
-- Must match the client patch built by client/tools/build_client_patch.py.

-- Server-side ChrRaces override: playable Horde race, two-headed ogre models (displays 3250 yellow, 19930 blue),
-- Orc data for everything the client takes from the race (sounds, language). No intro cinematic yet: the
-- Durotar one does not fit a start in Blade's Edge (a Blade's Edge fly-by is planned).
DELETE FROM `chrraces_dbc` WHERE `ID` = 9;
INSERT INTO `chrraces_dbc` (`ID`, `Flags`, `FactionID`, `ExplorationSoundID`, `MaleDisplayId`, `FemaleDisplayId`,
    `ClientPrefix`, `BaseLanguage`, `CreatureType`, `ResSicknessSpellID`, `SplashSoundID`, `ClientFilestring`,
    `CinematicSequenceID`, `Alliance`, `Name_Lang_enUS`, `Name_Lang_enGB`, `Name_Lang_koKR`, `Name_Lang_frFR`,
    `Name_Lang_deDE`, `Name_Lang_enCN`, `Name_Lang_zhCN`, `Name_Lang_enTW`, `Name_Lang_zhTW`, `Name_Lang_esES`,
    `Name_Lang_esMX`, `Name_Lang_ruRU`, `Name_Lang_ptPT`, `Name_Lang_ptBR`, `Name_Lang_itIT`, `Name_Lang_Unk`,
    `Name_Lang_Mask`, `Name_Female_Lang_enUS`, `Name_Female_Lang_enGB`, `Name_Female_Lang_koKR`,
    `Name_Female_Lang_frFR`, `Name_Female_Lang_deDE`, `Name_Female_Lang_enCN`, `Name_Female_Lang_zhCN`,
    `Name_Female_Lang_enTW`, `Name_Female_Lang_zhTW`, `Name_Female_Lang_esES`, `Name_Female_Lang_esMX`,
    `Name_Female_Lang_ruRU`, `Name_Female_Lang_ptPT`, `Name_Female_Lang_ptBR`, `Name_Female_Lang_itIT`,
    `Name_Female_Lang_Unk`, `Name_Female_Lang_Mask`, `Name_Male_Lang_enUS`, `Name_Male_Lang_enGB`,
    `Name_Male_Lang_koKR`, `Name_Male_Lang_frFR`, `Name_Male_Lang_deDE`, `Name_Male_Lang_enCN`,
    `Name_Male_Lang_zhCN`, `Name_Male_Lang_enTW`, `Name_Male_Lang_zhTW`, `Name_Male_Lang_esES`,
    `Name_Male_Lang_esMX`, `Name_Male_Lang_ruRU`, `Name_Male_Lang_ptPT`, `Name_Male_Lang_ptBR`,
    `Name_Male_Lang_itIT`, `Name_Male_Lang_Unk`, `Name_Male_Lang_Mask`, `FacialHairCustomization_1`,
    `FacialHairCustomization_2`, `HairCustomization`, `Required_Expansion`) VALUES
(9, 12, 2, 4141, 3250, 19930, 'Or', 1, 7, 15007, 1096, 'Orc', 0, 1, 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre',
    'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 16712190, 'Ogre', 'Ogre', 'Ogre',
    'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 16712190,
    'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre', 'Ogre',
    'Ogre', 'Ogre', 16712190, 'NORMAL', 'PIERCINGS', 'NORMAL', 0);

-- No class choice: the client always creates class 2 (Paladin, the mana "carrier" class).
-- Start in Blade's Edge Mountains, Thunderlord Stronghold, in front of Tor'chunk Twoclaws (first quest giver).
-- The start zone (levels 1-10) is set up by mod_two_headed_ogre_start_zone.sql and _quests.sql.
DELETE FROM `playercreateinfo` WHERE `race` = 9;
INSERT INTO `playercreateinfo` (`race`, `class`, `map`, `zone`, `position_x`, `position_y`, `position_z`, `orientation`) VALUES
(9, 2, 530, 3522, 2293.05, 6030.82, 142.7, 5.5);

-- Strong, tough, not very clever (two heads still count as one brain).
DELETE FROM `player_race_stats` WHERE `Race` = 9;
INSERT INTO `player_race_stats` (`Race`, `Strength`, `Agility`, `Stamina`, `Intellect`, `Spirit`) VALUES
(9, 4, -4, 3, -2, 0);

-- Orcish language (the race mask of the stock row does not include the Ogre).
DELETE FROM `playercreateinfo_skills` WHERE `raceMask` = 256 AND `classMask` = 0 AND `skill` = 109;
INSERT INTO `playercreateinfo_skills` (`raceMask`, `classMask`, `skill`, `rank`, `comment`) VALUES
(256, 0, 109, 0, 'Ogre - Language: Orcish');

-- Orc warrior starting gear: harness, pants, boots, hearthstone, two-handed axe.
-- The Brute (the Ogre's class: the Paladin carrier, renamed by the client patch): a cloth robe and two fist
-- weapons. The main hand one is equipped at creation, the module equips the off hand one at the first login
-- (dual wield is learned at login).
DELETE FROM `item_template` WHERE `entry` = 91003;
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `InventoryType`, `Material`, `sheath`, `ItemLevel`, `RequiredLevel`, `dmg_min1`, `dmg_max1`, `dmg_type1`, `delay`,
    `MaxDurability`, `SellPrice`, `bonding`, `description`, `VerifiedBuild`) VALUES
(91003, 2, 13, -1, 'Jointures de brute', 34557, 1, 13, 1, 7, 1, 1, 1, 3, 0, 2000, 20, 1, 0,
    'Deux têtes, quatre poings, aucune subtilité.', 0);

DELETE FROM `playercreateinfo_item` WHERE `race` = 9 AND `class` = 2;
INSERT INTO `playercreateinfo_item` (`race`, `class`, `itemid`, `amount`, `Note`) VALUES
(9, 2, 56, 1, 'Apprentice''s Robe'),
(9, 2, 91003, 1, 'Jointures de brute'),
(9, 2, 6948, 1, 'Hearthstone');

DELETE FROM `playercreateinfo_action` WHERE `race` = 9 AND `class` = 2;
INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`) VALUES
(9, 2, 0, 6603, 0),
(9, 2, 11, 6948, 128);
