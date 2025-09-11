-- Security setup script for MySQL
-- This script runs early in the initialization process

-- Create additional security measures
-- Remove anonymous users
DELETE FROM mysql.user WHERE User = '';

-- Remove test database
DROP DATABASE IF EXISTS test;

-- Remove privileges on test database
DELETE FROM mysql.db WHERE Db = 'test' OR Db = 'test\\_%';

-- Reload privileges
FLUSH PRIVILEGES;

SELECT 'Security setup completed' as status;