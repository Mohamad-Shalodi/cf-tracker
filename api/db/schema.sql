CREATE DATABASE IF NOT EXISTS cf_tracker;
USE cf_tracker;

CREATE TABLE IF NOT EXISTS user(
    id_user INTEGER AUTO_INCREMENT PRIMARY KEY,
    handle VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    last_synced_at TIMESTAMP NOT NULL DEFAULT '1970-01-01 00:00:01'
);

CREATE TABLE IF NOT EXISTS submission(
    id_submission INTEGER AUTO_INCREMENT PRIMARY KEY,
    id_user INTEGER NOT NULL,
    cf_reference INTEGER UNIQUE NOT NULL,
    problem_name VARCHAR(512) NOT NULL,
    problem_rate INTEGER NOT NULL,
    creation_time TIMESTAMP NOT NULL,
    FOREIGN KEY (id_user) REFERENCES user(id_user) ON DELETE CASCADE,
);
CREATE UNIQUE INDEX user_creation_time ON submission (id_user, creation_time);
