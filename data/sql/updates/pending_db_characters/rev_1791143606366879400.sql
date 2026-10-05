-- Shared control: extra accounts allowed to log into a character (see WorldSession::IsCopilot)
CREATE TABLE IF NOT EXISTS `character_shared_access` (
    `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid',
    `account` INT UNSIGNED NOT NULL COMMENT 'account allowed to log into the character besides its owner',
    PRIMARY KEY (`guid`, `account`),
    KEY `idx_account` (`account`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Accounts sharing control of a character';
