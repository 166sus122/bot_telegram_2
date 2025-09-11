-- Initial database setup for Pirate Content Bot
-- This file is executed when MySQL container starts for the first time

USE pirate_content;

-- Create basic tables if they don't exist (handled by migrations in the app)
-- This is just to ensure the database is properly initialized

-- Set timezone
SET GLOBAL time_zone = '+00:00';

-- Enable secure file operations
SET GLOBAL local_infile = 0;

-- Set proper character set
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

SELECT 'Database initialization completed' as status;