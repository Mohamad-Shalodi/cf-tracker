CREATE DATABASE IF NOT EXISTS cf_tracker;
USE cf_tracker;

CREATE TABLE IF NOT EXISTS user(
    id_user INTEGER AUTO_INCREMENT PRIMARY KEY,
    handle VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    image VARCHAR(256) NOT NULL,
    id_discord_user VARCHAR(50) UNIQUE NOT NULL,
    last_synced_at TIMESTAMP NOT NULL DEFAULT '1970-01-01 00:00:01'
);

CREATE TABLE IF NOT EXISTS submission(
    id_submission INTEGER AUTO_INCREMENT PRIMARY KEY,
    id_user INTEGER NOT NULL,
    problem_key varchar(50) NOT NULL,
    problem_rate INTEGER NOT NULL,
    creation_time TIMESTAMP NOT NULL,
    FOREIGN KEY (id_user) REFERENCES user(id_user) ON DELETE CASCADE,
    UNIQUE KEY user_problem (id_user, problem_key)
);
CREATE UNIQUE INDEX user_creation_time ON submission (id_user, creation_time);

CREATE TABLE IF NOT EXISTS html_content(
    id_html_content INTEGER AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    html TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_call(
    id_user_call INTEGER AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_user INTEGER NOT NULL, 
    FOREIGN KEY (id_user) REFERENCES user(id_user) ON DELETE CASCADE
);


