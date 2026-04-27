ALTER TABLE tblSearchSessions
    ADD COLUMN save_mode VARCHAR(20) NULL DEFAULT 'whole';

ALTER TABLE tblSearchSessions
    ADD CONSTRAINT ck_search_save_mode CHECK (save_mode IN ('whole', 'single'));

UPDATE tblSearchSessions
SET save_mode = CASE
    WHEN title LIKE 'Bedrijf: %' OR title LIKE 'Vacature: %' THEN 'single'
    ELSE 'whole'
END
WHERE save_mode IS NULL OR save_mode = '';
