-- Fix tblSearchResults: make vacature_id nullable so bedrijf results can have vacature_id=NULL
-- The CHECK constraint ck_results_target requires vacature_id IS NULL for bedrijf results

-- Drop foreign keys first
ALTER TABLE tblSearchResults DROP FOREIGN KEY fk_results_vac;
ALTER TABLE tblSearchResults DROP FOREIGN KEY fk_results_bedrijf;

-- Make vacature_id nullable
ALTER TABLE tblSearchResults MODIFY COLUMN vacature_id VARCHAR(100) DEFAULT NULL;

-- Re-add foreign keys (now both nullable)
ALTER TABLE tblSearchResults ADD CONSTRAINT fk_results_vac
    FOREIGN KEY (vacature_id) REFERENCES tblVacatures(interne_referentie) ON DELETE CASCADE;
ALTER TABLE tblSearchResults ADD CONSTRAINT fk_results_bedrijf
    FOREIGN KEY (bedrijf_id) REFERENCES tblBedrijven(id) ON DELETE CASCADE;
