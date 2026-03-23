USE `InfoSearch`;

-- Safe, backwards-compatible optimization:
-- Add lookup indexes for filters by job domain and work schedule.
-- These are guarded so the file remains repeatable outside the migration runner too.

SET @create_ix_vjd := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'tblVacatureJobdomeinen'
        AND index_name = 'ix_vjd_jobdomein'
    ),
    'SELECT ''skip ix_vjd_jobdomein''',
    'CREATE INDEX `ix_vjd_jobdomein` ON `tblVacatureJobdomeinen` (`jobdomein`)'
  )
);
PREPARE stmt_vjd FROM @create_ix_vjd;
EXECUTE stmt_vjd;
DEALLOCATE PREPARE stmt_vjd;

SET @create_ix_vst := (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = DATABASE()
        AND table_name = 'tblVacatureStelsels'
        AND index_name = 'ix_vst_stelsel'
    ),
    'SELECT ''skip ix_vst_stelsel''',
    'CREATE INDEX `ix_vst_stelsel` ON `tblVacatureStelsels` (`stelsel`)'
  )
);
PREPARE stmt_vst FROM @create_ix_vst;
EXECUTE stmt_vst;
DEALLOCATE PREPARE stmt_vst;
