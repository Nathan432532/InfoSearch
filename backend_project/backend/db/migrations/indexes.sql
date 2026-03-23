USE `InfoSearch`;

-- Idempotent, repeatable index migration.
-- Uses information_schema checks to avoid duplicate key errors on rerun.

SET @create_ix_bedrijven_nace := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblBedrijven' AND index_name = 'ix_bedrijven_nace'),
    'SELECT ''skip ix_bedrijven_nace''',
    'CREATE INDEX `ix_bedrijven_nace` ON `tblBedrijven` (`nace_code`)'
  )
);
PREPARE stmt FROM @create_ix_bedrijven_nace; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_bedrijven_email := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblBedrijven' AND index_name = 'ix_bedrijven_email'),
    'SELECT ''skip ix_bedrijven_email''',
    'CREATE INDEX `ix_bedrijven_email` ON `tblBedrijven` (`email`)'
  )
);
PREPARE stmt FROM @create_ix_bedrijven_email; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_bedrijven_telefoon := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblBedrijven' AND index_name = 'ix_bedrijven_telefoon'),
    'SELECT ''skip ix_bedrijven_telefoon''',
    'CREATE INDEX `ix_bedrijven_telefoon` ON `tblBedrijven` (`telefoon`)'
  )
);
PREPARE stmt FROM @create_ix_bedrijven_telefoon; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_bedrijven_source_code := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblBedrijven' AND index_name = 'ix_bedrijven_source_code'),
    'SELECT ''skip ix_bedrijven_source_code''',
    'CREATE INDEX `ix_bedrijven_source_code` ON `tblBedrijven` (`source_code`)'
  )
);
PREPARE stmt FROM @create_ix_bedrijven_source_code; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_vacatures_status_datum := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblVacatures' AND index_name = 'ix_vacatures_status_datum'),
    'SELECT ''skip ix_vacatures_status_datum''',
    'CREATE INDEX `ix_vacatures_status_datum` ON `tblVacatures` (`status`, `publicatie_datum`)'
  )
);
PREPARE stmt FROM @create_ix_vacatures_status_datum; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_vacatures_gemeente_datum := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblVacatures' AND index_name = 'ix_vacatures_gemeente_datum'),
    'SELECT ''skip ix_vacatures_gemeente_datum''',
    'CREATE INDEX `ix_vacatures_gemeente_datum` ON `tblVacatures` (`gemeente`, `publicatie_datum`)'
  )
);
PREPARE stmt FROM @create_ix_vacatures_gemeente_datum; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_vacatures_provincie_datum := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblVacatures' AND index_name = 'ix_vacatures_provincie_datum'),
    'SELECT ''skip ix_vacatures_provincie_datum''',
    'CREATE INDEX `ix_vacatures_provincie_datum` ON `tblVacatures` (`provincie`, `publicatie_datum`)'
  )
);
PREPARE stmt FROM @create_ix_vacatures_provincie_datum; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_vacatures_bedrijf_datum := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblVacatures' AND index_name = 'ix_vacatures_bedrijf_datum'),
    'SELECT ''skip ix_vacatures_bedrijf_datum''',
    'CREATE INDEX `ix_vacatures_bedrijf_datum` ON `tblVacatures` (`bedrijf_id`, `publicatie_datum`)'
  )
);
PREPARE stmt FROM @create_ix_vacatures_bedrijf_datum; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_vacatures_contract := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblVacatures' AND index_name = 'ix_vacatures_contract'),
    'SELECT ''skip ix_vacatures_contract''',
    'CREATE INDEX `ix_vacatures_contract` ON `tblVacatures` (`contract_type`, `contract_regime`)'
  )
);
PREPARE stmt FROM @create_ix_vacatures_contract; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_search_user_type_created := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblSearchSessions' AND index_name = 'ix_search_user_type_created'),
    'SELECT ''skip ix_search_user_type_created''',
    'CREATE INDEX `ix_search_user_type_created` ON `tblSearchSessions` (`user_id`, `type`, `created_at`)'
  )
);
PREPARE stmt FROM @create_ix_search_user_type_created; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_results_search_score := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblSearchResults' AND index_name = 'ix_results_search_score'),
    'SELECT ''skip ix_results_search_score''',
    'CREATE INDEX `ix_results_search_score` ON `tblSearchResults` (`search_id`, `match_score`)'
  )
);
PREPARE stmt FROM @create_ix_results_search_score; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_feedback_user_created := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblFeedback' AND index_name = 'ix_feedback_user_created'),
    'SELECT ''skip ix_feedback_user_created''',
    'CREATE INDEX `ix_feedback_user_created` ON `tblFeedback` (`user_id`, `created_at`)'
  )
);
PREPARE stmt FROM @create_ix_feedback_user_created; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_feedback_search_created := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblFeedback' AND index_name = 'ix_feedback_search_created'),
    'SELECT ''skip ix_feedback_search_created''',
    'CREATE INDEX `ix_feedback_search_created` ON `tblFeedback` (`search_id`, `created_at`)'
  )
);
PREPARE stmt FROM @create_ix_feedback_search_created; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_entitytags_type_tag := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblEntityTags' AND index_name = 'ix_entitytags_type_tag'),
    'SELECT ''skip ix_entitytags_type_tag''',
    'CREATE INDEX `ix_entitytags_type_tag` ON `tblEntityTags` (`entity_type`, `tag_id`)'
  )
);
PREPARE stmt FROM @create_ix_entitytags_type_tag; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_embeddings_model_version := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblEmbeddings' AND index_name = 'ix_embeddings_model_version'),
    'SELECT ''skip ix_embeddings_model_version''',
    'CREATE INDEX `ix_embeddings_model_version` ON `tblEmbeddings` (`model_name`, `model_version`)'
  )
);
PREPARE stmt FROM @create_ix_embeddings_model_version; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_crm_btw := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblCRM_Bedrijven' AND index_name = 'ix_crm_btw'),
    'SELECT ''skip ix_crm_btw''',
    'CREATE INDEX `ix_crm_btw` ON `tblCRM_Bedrijven` (`btw_nummer`)'
  )
);
PREPARE stmt FROM @create_ix_crm_btw; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_crm_email := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblCRM_Bedrijven' AND index_name = 'ix_crm_email'),
    'SELECT ''skip ix_crm_email''',
    'CREATE INDEX `ix_crm_email` ON `tblCRM_Bedrijven` (`email`)'
  )
);
PREPARE stmt FROM @create_ix_crm_email; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_cv_user_created := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblCvProfiles' AND index_name = 'ix_cv_user_created'),
    'SELECT ''skip ix_cv_user_created''',
    'CREATE INDEX `ix_cv_user_created` ON `tblCvProfiles` (`user_id`, `created_at`)'
  )
);
PREPARE stmt FROM @create_ix_cv_user_created; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @create_ix_project_user_created := (
  SELECT IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'tblProjectBriefs' AND index_name = 'ix_project_user_created'),
    'SELECT ''skip ix_project_user_created''',
    'CREATE INDEX `ix_project_user_created` ON `tblProjectBriefs` (`user_id`, `created_at`)'
  )
);
PREPARE stmt FROM @create_ix_project_user_created; EXECUTE stmt; DEALLOCATE PREPARE stmt;