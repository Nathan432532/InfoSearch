/* ============================================================================
   004 — AI enrichment columns on tblBedrijven
   Tracks Qwen-extracted company profiles so we know which companies
   have already been processed and can do incremental weekly updates.
   ============================================================================ */

USE `InfoSearch`;

ALTER TABLE `tblBedrijven`
  ADD COLUMN `sector`             VARCHAR(150) NULL AFTER `type`,
  ADD COLUMN `ai_beschrijving`    TEXT NULL AFTER `sector`,
  ADD COLUMN `tech_stack_json`    JSON NULL AFTER `ai_beschrijving`,
  ADD COLUMN `machine_park_json`  JSON NULL AFTER `tech_stack_json`,
  ADD COLUMN `business_trigger`   TEXT NULL AFTER `machine_park_json`,
  ADD COLUMN `keywords_json`      JSON NULL AFTER `business_trigger`,
  ADD COLUMN `ai_enriched_at`     TIMESTAMP NULL AFTER `keywords_json`;

CREATE INDEX `ix_bedrijven_ai_enriched` ON `tblBedrijven` (`ai_enriched_at`);
