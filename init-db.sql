-- 🏴‍☠️ אתחול מסד נתונים אוטומטי לבוט התמימים הפיראטים
-- קובץ זה רץ אוטומטית כשהמערכת עולה לראשונה

-- יצירת טבלת משתמשים
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    total_requests INT DEFAULT 0,
    fulfilled_requests INT DEFAULT 0,
    rejected_requests INT DEFAULT 0,
    reputation_score INT DEFAULT 50,
    is_banned BOOLEAN DEFAULT FALSE,
    warnings_count INT DEFAULT 0,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- יצירת טבלת בקשות
CREATE TABLE IF NOT EXISTS requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(500) NOT NULL,
    content_text TEXT NOT NULL,
    original_text TEXT,
    category VARCHAR(100) DEFAULT 'general',
    subcategory VARCHAR(100),
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('pending', 'processing', 'fulfilled', 'rejected', 'cancelled') DEFAULT 'pending',
    confidence_score FLOAT DEFAULT 0.0,
    source_type ENUM('private', 'group', 'channel') DEFAULT 'private',
    source_id BIGINT,
    message_id INT,
    notes TEXT,
    episode VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fulfilled_at TIMESTAMP NULL,
    processed_by BIGINT,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at),
    INDEX idx_title (title(100)),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- יצירת טבלת דירוגים
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    user_id BIGINT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rating (request_id, user_id),
    INDEX idx_request_id (request_id),
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- יצירת טבלת כפילויות
CREATE TABLE IF NOT EXISTS duplicates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    original_request_id INT NOT NULL,
    duplicate_request_id INT NOT NULL,
    similarity_score FLOAT DEFAULT 0.0,
    status ENUM('pending', 'confirmed', 'rejected') DEFAULT 'pending',
    reviewed_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (original_request_id) REFERENCES requests(id) ON DELETE CASCADE,
    FOREIGN KEY (duplicate_request_id) REFERENCES requests(id) ON DELETE CASCADE,
    UNIQUE KEY unique_duplicate_pair (original_request_id, duplicate_request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- יצירת טבלת מיגרציות
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_version (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- יצירת טבלת סטטיסטיקות מערכת
CREATE TABLE IF NOT EXISTS system_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_name VARCHAR(100) UNIQUE NOT NULL,
    stat_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stat_name (stat_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- הוספת מיגרציות בסיסיות
INSERT IGNORE INTO schema_migrations (version) VALUES 
('001_initial_schema'),
('002_add_ratings_table'),
('003_add_user_stats'),
('004_add_request_metadata'),
('005_add_source_tracking'),
('006_add_duplicates_table'),
('007_add_priority_system'),
('008_add_reputation_system'),
('009_add_advanced_indexing'),
('010_add_system_stats'),
('011_add_episode_column');

-- הוספת נתוני ברירת מחדל לסטטיסטיקות
INSERT IGNORE INTO system_stats (stat_name, stat_value) VALUES
('total_requests', '0'),
('total_users', '0'),
('system_version', '2.0.0'),
('last_backup', ''),
('maintenance_mode', 'false');

-- יצירת משתמש אדמין ברירת מחדל (אם לא קיים)
INSERT IGNORE INTO users (user_id, username, first_name, total_requests, reputation_score, first_seen, last_seen) 
VALUES (6562280181, 'admin', 'Admin User', 0, 100, NOW(), NOW());

-- הודעת הצלחה
SELECT 'Database initialized successfully! All tables created.' as status;
SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'pirate_content';