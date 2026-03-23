/* ============================================================================
   InfoSearch — MySQL 8.0+ schema (Local + Azure MySQL Flexible Server)
   match_score: 1.00 .. 10.00 (or NULL when not computed yet)
   ============================================================================ */

CREATE DATABASE IF NOT EXISTS `InfoSearch`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE `InfoSearch`;

-- Optional: keep defaults safe/clear for CI/CD runs
SET sql_safe_updates = 0;

-- ----------------------------------------------------------------------------
-- 1) Users (Easy Auth / Azure AD)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblUsers` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `auth_provider` VARCHAR(50) NOT NULL DEFAULT 'azure_easy_auth',
  `auth_subject` VARCHAR(200) NOT NULL,          -- oid/sub from token
  `email` VARCHAR(255) NULL,
  `display_name` VARCHAR(255) NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',    -- user|admin
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_provider_subject` (`auth_provider`, `auth_subject`),
  KEY `ix_users_email` (`email`),
  CONSTRAINT `ck_users_role` CHECK (`role` IN ('user','admin'))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2) Sources (provenance)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblSources` (
  `id` TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(30) NOT NULL,       -- vdab|kbo|crm|resumereader
  `name` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sources_code` (`code`)
) ENGINE=InnoDB;

INSERT IGNORE INTO `tblSources` (`code`,`name`) VALUES
('vdab','VDAB'),
('kbo','Kruispuntbank van Ondernemingen'),
('crm','InfoFarm CRM'),
('resumereader','ResumeReader API');

-- ----------------------------------------------------------------------------
-- 3) Companies (canonical)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblBedrijven` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `kbo_nummer` VARCHAR(20) NULL,                    -- UNIQUE if present
  `naam` VARCHAR(255) NOT NULL,
  `type` VARCHAR(50) NULL,                          -- e.g. GEWONE_BEDRIJVEN
  `nace_code` VARCHAR(20) NULL,
  `website` VARCHAR(500) NULL,
  `email` VARCHAR(255) NULL,
  `telefoon` VARCHAR(50) NULL,

  `adres_postcode` VARCHAR(10) NULL,
  `adres_gemeente` VARCHAR(100) NULL,
  `adres_provincie` VARCHAR(100) NULL,
  `adres_landcode` CHAR(2) NULL DEFAULT 'BE',
  `lat` DOUBLE NULL,
  `lon` DOUBLE NULL,

  `source_code` VARCHAR(30) NULL DEFAULT 'vdab',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_bedrijven_kbo` (`kbo_nummer`),
  KEY `ix_bedrijven_naam` (`naam`),
  KEY `ix_bedrijven_loc` (`adres_postcode`, `adres_gemeente`),
  CONSTRAINT `ck_bedrijven_source` CHECK (`source_code` IN ('vdab','kbo','crm','resumereader') OR `source_code` IS NULL)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4) CRM mirror (optional) + mapping
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblCRM_Bedrijven` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `naam` VARCHAR(255) NOT NULL,
  `btw_nummer` VARCHAR(50) NULL,
  `kbo_nummer` VARCHAR(20) NULL,
  `email` VARCHAR(255) NULL,
  `telefoon` VARCHAR(50) NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'lead',     -- lead|prospect|klant
  `raw_json` JSON NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_crm_kbo` (`kbo_nummer`),
  KEY `ix_crm_status` (`status`),
  CONSTRAINT `ck_crm_status` CHECK (`status` IN ('lead','prospect','klant'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `tblCRM_BedrijfMap` (
  `crm_bedrijf_id` BIGINT UNSIGNED NOT NULL,
  `bedrijf_id` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`crm_bedrijf_id`, `bedrijf_id`),
  CONSTRAINT `fk_crmmap_crm` FOREIGN KEY (`crm_bedrijf_id`) REFERENCES `tblCRM_Bedrijven` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_crmmap_bedrijf` FOREIGN KEY (`bedrijf_id`) REFERENCES `tblBedrijven` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5) Vacancies (VDAB) — PK is interneReferentie UUID
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblVacatures` (
  `interne_referentie` CHAR(36) NOT NULL,
  `vdab_referentie` BIGINT NULL,
  `status` VARCHAR(30) NULL,
  `publicatie_datum` DATE NULL,

  `bron` VARCHAR(50) NULL,
  `internationaal_opengesteld` BOOLEAN NULL,

  `titel` VARCHAR(255) NOT NULL,
  `beroep` VARCHAR(255) NULL,
  `ervaring` VARCHAR(255) NULL,
  `omschrijving` MEDIUMTEXT NULL,
  `vrije_vereiste` MEDIUMTEXT NULL,

  `contract_type` VARCHAR(100) NULL,
  `contract_regime` VARCHAR(100) NULL,
  `aantal_uur` INT NULL,
  `vermoedelijke_startdatum` DATETIME NULL,
  `loon_min` DECIMAL(12,2) NULL,
  `loon_max` DECIMAL(12,2) NULL,
  `contract_extra` MEDIUMTEXT NULL,

  `postcode` VARCHAR(10) NULL,
  `gemeente` VARCHAR(100) NULL,
  `provincie` VARCHAR(100) NULL,
  `lat` DOUBLE NULL,
  `lon` DOUBLE NULL,

  `cv_gewenst` BOOLEAN NULL,
  `sollicitatie_email` VARCHAR(255) NULL,
  `sollicitatie_webformulier` VARCHAR(500) NULL,
  `sollicitatie_telefoon` VARCHAR(50) NULL,

  `bedrijf_id` BIGINT UNSIGNED NULL,

  `raw_json` JSON NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`interne_referentie`),
  UNIQUE KEY `uq_vacatures_vdab_ref` (`vdab_referentie`),
  KEY `ix_vacatures_bedrijf` (`bedrijf_id`),
  KEY `ix_vacatures_datum` (`publicatie_datum`),
  KEY `ix_vacatures_loc` (`postcode`, `gemeente`),
  FULLTEXT KEY `ft_vacatures_text` (`titel`, `omschrijving`, `vrije_vereiste`),

  CONSTRAINT `fk_vac_bedrijf`
    FOREIGN KEY (`bedrijf_id`) REFERENCES `tblBedrijven` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB;

-- job.jobdomeinen[]
CREATE TABLE IF NOT EXISTS `tblVacatureJobdomeinen` (
  `interne_referentie` CHAR(36) NOT NULL,
  `jobdomein` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`interne_referentie`, `jobdomein`),
  CONSTRAINT `fk_vjd_vac` FOREIGN KEY (`interne_referentie`)
    REFERENCES `tblVacatures` (`interne_referentie`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- contract.stelsel[]
CREATE TABLE IF NOT EXISTS `tblVacatureStelsels` (
  `interne_referentie` CHAR(36) NOT NULL,
  `stelsel` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`interne_referentie`, `stelsel`),
  CONSTRAINT `fk_vst_vac` FOREIGN KEY (`interne_referentie`)
    REFERENCES `tblVacatures` (`interne_referentie`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6) Unified tags system (skills/technologie/talen/studies/...)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblTags` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `type` VARCHAR(50) NOT NULL,      -- skill|technology|taal|rijbewijs|studie|attest|...
  `naam` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_tags_type_naam` (`type`, `naam`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `tblEntityTags` (
  `entity_type` VARCHAR(30) NOT NULL,             -- vacature|bedrijf|cv|project
  `entity_id` VARCHAR(100) NOT NULL,              -- vacature UUID, bedrijf_id (as string), cv_id, project_id
  `tag_id` BIGINT UNSIGNED NOT NULL,
  `extra_json` JSON NULL,                         -- e.g. {"niveau":"zeer goed"} for languages
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`entity_type`, `entity_id`, `tag_id`),
  KEY `ix_entitytags_tag` (`tag_id`),
  KEY `ix_entitytags_entity` (`entity_type`, `entity_id`),
  CONSTRAINT `fk_entitytags_tag` FOREIGN KEY (`tag_id`) REFERENCES `tblTags` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_entity_type` CHECK (`entity_type` IN ('vacature','bedrijf','cv','project'))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7) CV profiles (ResumeReader structured output)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblCvProfiles` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `title` VARCHAR(255) NULL,
  `source_blob_url` VARCHAR(1000) NULL,
  `parsed_json` JSON NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_cv_user` (`user_id`),
  CONSTRAINT `fk_cv_user` FOREIGN KEY (`user_id`) REFERENCES `tblUsers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8) Project briefs (customer search flow)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblProjectBriefs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `title` VARCHAR(255) NULL,
  `description_text` MEDIUMTEXT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_project_user` (`user_id`),
  FULLTEXT KEY `ft_project_text` (`description_text`),
  CONSTRAINT `fk_project_user` FOREIGN KEY (`user_id`) REFERENCES `tblUsers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 9) Saved searches
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblSearchSessions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `type` VARCHAR(20) NOT NULL,                    -- cv|project
  `title` VARCHAR(255) NULL,
  `input_text` MEDIUMTEXT NULL,
  `filters_json` JSON NULL,
  `cv_profile_id` BIGINT UNSIGNED NULL,
  `project_brief_id` BIGINT UNSIGNED NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_search_user` (`user_id`),
  KEY `ix_search_type_created` (`type`, `created_at`),
  CONSTRAINT `ck_search_type` CHECK (`type` IN ('cv','project')),
  CONSTRAINT `fk_search_user` FOREIGN KEY (`user_id`) REFERENCES `tblUsers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_search_cv` FOREIGN KEY (`cv_profile_id`) REFERENCES `tblCvProfiles` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_search_project` FOREIGN KEY (`project_brief_id`) REFERENCES `tblProjectBriefs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 10) Search results (prospect list)
-- match_score: 1.00..10.00 OR NULL
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblSearchResults` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `search_id` BIGINT UNSIGNED NOT NULL,
  `result_type` VARCHAR(20) NOT NULL,              -- vacature|bedrijf
  `vacature_id` CHAR(36) NULL,
  `bedrijf_id` BIGINT UNSIGNED NULL,
  `rank` INT NOT NULL,
  `match_score` DECIMAL(4,2) NULL,                 -- 1.00..10.00
  `explanation_json` JSON NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_search_rank` (`search_id`, `rank`),
  KEY `ix_results_search` (`search_id`),
  KEY `ix_results_vac` (`vacature_id`),
  KEY `ix_results_bedrijf` (`bedrijf_id`),

  CONSTRAINT `ck_result_type` CHECK (`result_type` IN ('vacature','bedrijf')),
  CONSTRAINT `fk_results_search` FOREIGN KEY (`search_id`) REFERENCES `tblSearchSessions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_results_vac` FOREIGN KEY (`vacature_id`) REFERENCES `tblVacatures` (`interne_referentie`) ON DELETE CASCADE,
  CONSTRAINT `fk_results_bedrijf` FOREIGN KEY (`bedrijf_id`) REFERENCES `tblBedrijven` (`id`) ON DELETE CASCADE,

  -- exactly one target must be set
  CONSTRAINT `ck_results_target` CHECK (
    (`result_type` = 'vacature' AND `vacature_id` IS NOT NULL AND `bedrijf_id` IS NULL)
    OR
    (`result_type` = 'bedrijf' AND `bedrijf_id` IS NOT NULL AND `vacature_id` IS NULL)
  ),

  -- match_score must be 1..10 when present
  CONSTRAINT `ck_results_score` CHECK (`match_score` IS NULL OR (`match_score` >= 1.00 AND `match_score` <= 10.00))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 11) Feedback (thumbs up/down per prospect)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblFeedback` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `search_id` BIGINT UNSIGNED NOT NULL,
  `result_type` VARCHAR(20) NOT NULL,              -- vacature|bedrijf
  `vacature_id` CHAR(36) NULL,
  `bedrijf_id` BIGINT UNSIGNED NULL,
  `label` TINYINT NOT NULL,                        -- 1=up, 0=down
  `comment` VARCHAR(1000) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_feedback_once` (`user_id`, `search_id`, `result_type`, `vacature_id`, `bedrijf_id`),
  KEY `ix_feedback_search` (`search_id`),

  CONSTRAINT `ck_feedback_type` CHECK (`result_type` IN ('vacature','bedrijf')),
  CONSTRAINT `ck_feedback_label` CHECK (`label` IN (0,1)),
  CONSTRAINT `fk_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `tblUsers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_feedback_search` FOREIGN KEY (`search_id`) REFERENCES `tblSearchSessions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_feedback_vac` FOREIGN KEY (`vacature_id`) REFERENCES `tblVacatures` (`interne_referentie`) ON DELETE CASCADE,
  CONSTRAINT `fk_feedback_bedrijf` FOREIGN KEY (`bedrijf_id`) REFERENCES `tblBedrijven` (`id`) ON DELETE CASCADE,

  CONSTRAINT `ck_feedback_target` CHECK (
    (`result_type` = 'vacature' AND `vacature_id` IS NOT NULL AND `bedrijf_id` IS NULL)
    OR
    (`result_type` = 'bedrijf' AND `bedrijf_id` IS NOT NULL AND `vacature_id` IS NULL)
  )
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 12) Embeddings (SBERT vectors) — store as JSON array (MVP)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblEmbeddings` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `entity_type` VARCHAR(30) NOT NULL,              -- vacature|bedrijf|cv|project
  `entity_id` VARCHAR(100) NOT NULL,
  `model_name` VARCHAR(100) NOT NULL DEFAULT 'sentence-bert',
  `model_version` VARCHAR(50) NOT NULL,
  `vector_json` JSON NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_embedding_entity_model` (`entity_type`, `entity_id`, `model_name`, `model_version`),
  CONSTRAINT `ck_embed_entity_type` CHECK (`entity_type` IN ('vacature','bedrijf','cv','project'))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 13) Model training runs (admin retraining audit)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tblModelRuns` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `triggered_by_user_id` BIGINT UNSIGNED NULL,
  `model_name` VARCHAR(100) NOT NULL,          -- random-forest, etc.
  `model_version` VARCHAR(50) NOT NULL,
  `params_json` JSON NULL,
  `metrics_json` JSON NULL,
  `notes` VARCHAR(1000) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_modelruns_created` (`created_at`),
  CONSTRAINT `fk_modelruns_user` FOREIGN KEY (`triggered_by_user_id`) REFERENCES `tblUsers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 14) Helpful indexes
-- ----------------------------------------------------------------------------
CREATE INDEX `ix_vacatures_status` ON `tblVacatures` (`status`);
CREATE INDEX `ix_vacatures_internationaal` ON `tblVacatures` (`internationaal_opengesteld`);

-- ----------------------------------------------------------------------------
-- Notes:
-- - CHECK constraints are enforced in MySQL 8.0.16+. Azure MySQL 8.0 supports this.
-- - JSON type supported in MySQL 8.0 (local + Azure).
-- - FULLTEXT supported (InnoDB). If you don’t need it yet, you can drop the FULLTEXT keys.
-- ----------------------------------------------------------------------------