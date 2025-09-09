-- Database initialization for Pirate Content Bot
-- This script creates the basic tables required for the bot to function

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS pirate_content CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pirate_content;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Content Requests Table
CREATE TABLE IF NOT EXISTS content_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    original_text TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    confidence INT DEFAULT 50,
    year INT NULL,
    season INT NULL,
    episode INT NULL,
    quality VARCHAR(20) NULL,
    language_pref VARCHAR(10) DEFAULT 'hebrew',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fulfilled_at TIMESTAMP NULL,
    fulfilled_by BIGINT NULL,
    rejected_by BIGINT NULL,
    notes TEXT NULL,
    rejection_reason TEXT NULL,
    
    INDEX user_idx (user_id),
    INDEX status_idx (status),
    INDEX category_idx (category),
    INDEX created_idx (created_at),
    INDEX title_idx (title(100)),
    FULLTEXT(title, original_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    total_requests INT DEFAULT 0,
    fulfilled_requests INT DEFAULT 0,
    rejected_requests INT DEFAULT 0,
    reputation_score INT DEFAULT 50,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT NULL,
    ban_until TIMESTAMP NULL,
    warnings_count INT DEFAULT 0,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_request_at TIMESTAMP NULL,
    
    INDEX username_idx (username),
    INDEX reputation_idx (reputation_score),
    INDEX banned_idx (is_banned),
    INDEX last_seen_idx (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Content Ratings Table
CREATE TABLE IF NOT EXISTS content_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    user_id BIGINT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_request (user_id, request_id),
    FOREIGN KEY (request_id) REFERENCES content_requests(id) ON DELETE CASCADE,
    INDEX request_idx (request_id),
    INDEX user_idx (user_id),
    INDEX rating_idx (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Schema Migrations Table (for migration tracking)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT DEFAULT 0,
    checksum VARCHAR(64) NULL,
    
    INDEX executed_idx (executed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert initial migration record
INSERT IGNORE INTO schema_migrations (version, description) 
VALUES ('001_create_basic_tables', 'Create basic content tables');

-- Create default admin user (optional)
-- INSERT IGNORE INTO users (user_id, username, first_name, reputation_score) 
-- VALUES (6039349310, 'admin1', 'Admin', 100);

COMMIT;