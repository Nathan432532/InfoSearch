-- Widen interne_referentie from CHAR(36) to VARCHAR(100) to accommodate
-- all VDAB vacancy reference formats.

-- Drop foreign keys that reference tblVacatures.interne_referentie
ALTER TABLE tblVacatureJobdomeinen DROP FOREIGN KEY fk_vjd_vac;
ALTER TABLE tblVacatureStelsels    DROP FOREIGN KEY fk_vst_vac;
ALTER TABLE tblSearchResults       DROP FOREIGN KEY fk_results_vac;
ALTER TABLE tblFeedback            DROP FOREIGN KEY fk_feedback_vac;

-- Widen columns
ALTER TABLE tblVacatures           MODIFY COLUMN interne_referentie VARCHAR(100) NOT NULL;
ALTER TABLE tblVacatureJobdomeinen MODIFY COLUMN interne_referentie VARCHAR(100) NOT NULL;
ALTER TABLE tblVacatureStelsels    MODIFY COLUMN interne_referentie VARCHAR(100) NOT NULL;
ALTER TABLE tblSearchResults       MODIFY COLUMN vacature_id        VARCHAR(100) NOT NULL;
ALTER TABLE tblFeedback            MODIFY COLUMN vacature_id        VARCHAR(100) NOT NULL;

-- Re-add foreign keys
ALTER TABLE tblVacatureJobdomeinen
  ADD CONSTRAINT fk_vjd_vac FOREIGN KEY (interne_referentie)
    REFERENCES tblVacatures (interne_referentie) ON DELETE CASCADE;

ALTER TABLE tblVacatureStelsels
  ADD CONSTRAINT fk_vst_vac FOREIGN KEY (interne_referentie)
    REFERENCES tblVacatures (interne_referentie) ON DELETE CASCADE;

ALTER TABLE tblSearchResults
  ADD CONSTRAINT fk_results_vac FOREIGN KEY (vacature_id)
    REFERENCES tblVacatures (interne_referentie) ON DELETE CASCADE;

ALTER TABLE tblFeedback
  ADD CONSTRAINT fk_feedback_vac FOREIGN KEY (vacature_id)
    REFERENCES tblVacatures (interne_referentie) ON DELETE CASCADE;
