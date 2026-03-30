-- Allow 'company' and 'job' as search types alongside 'cv' and 'project'
ALTER TABLE tblSearchSessions DROP CONSTRAINT ck_search_type;
ALTER TABLE tblSearchSessions ADD CONSTRAINT ck_search_type CHECK (`type` IN ('cv','project','company','job'));
