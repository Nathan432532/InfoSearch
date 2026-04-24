ALTER TABLE tblUsers
    ADD COLUMN display_name VARCHAR(255) NULL;

CREATE TABLE IF NOT EXISTS tblLocalUsers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash CHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_local_users_user_id (user_id),
    UNIQUE KEY uq_local_users_username (username),
    CONSTRAINT fk_local_users_user FOREIGN KEY (user_id) REFERENCES tblUsers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tblLocalSessions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    local_user_id BIGINT UNSIGNED NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_local_sessions_token (session_token),
    KEY ix_local_sessions_user_exp (local_user_id, expires_at),
    CONSTRAINT fk_local_sessions_user FOREIGN KEY (local_user_id) REFERENCES tblLocalUsers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT INTO tblUsers (id, auth_provider, auth_subject, email, display_name, role)
VALUES
    (2, 'local', 'local:admin', 'admin@infosearch.local', 'Admin', 'admin'),
    (3, 'local', 'local:jan', 'jan@infosearch.local', 'Jan', 'user')
ON DUPLICATE KEY UPDATE
    email = VALUES(email),
    display_name = VALUES(display_name),
    role = VALUES(role);

INSERT INTO tblLocalUsers (user_id, username, password_hash, is_active)
VALUES
    (2, 'admin', '5c06eb3d5a05a19f49476d694ca81a36344660e9d5b98e3d6a6630f31c2422e7', TRUE),
    (3, 'jan', 'fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4', TRUE)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    is_active = VALUES(is_active);

DELETE FROM tblLocalSessions WHERE expires_at <= UTC_TIMESTAMP();
