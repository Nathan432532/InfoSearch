-- Insert default local user for search sessions (hardcoded user_id=1)
INSERT IGNORE INTO tblUsers (id, auth_provider, auth_subject, email, role)
VALUES (1, 'local', 'default', 'test@infosearch.local', 'user');
