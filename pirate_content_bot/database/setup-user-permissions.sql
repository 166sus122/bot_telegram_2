-- Setup user permissions for all possible connections
-- This ensures the pirate_user can connect from any host

-- Create user with correct permissions for Docker environment
CREATE USER IF NOT EXISTS 'pirate_user'@'%' IDENTIFIED BY 'test_password_123';
CREATE USER IF NOT EXISTS 'pirate_user'@'localhost' IDENTIFIED BY 'test_password_123';
CREATE USER IF NOT EXISTS 'pirate_user'@'172.18.0.1' IDENTIFIED BY 'test_password_123';
CREATE USER IF NOT EXISTS 'pirate_user'@'172.%' IDENTIFIED BY 'test_password_123';

-- Grant full privileges on pirate_content database
GRANT ALL PRIVILEGES ON pirate_content.* TO 'pirate_user'@'%';
GRANT ALL PRIVILEGES ON pirate_content.* TO 'pirate_user'@'localhost'; 
GRANT ALL PRIVILEGES ON pirate_content.* TO 'pirate_user'@'172.18.0.1';
GRANT ALL PRIVILEGES ON pirate_content.* TO 'pirate_user'@'172.%';

-- Grant specific permissions needed
GRANT CREATE, DROP, ALTER, INDEX ON pirate_content.* TO 'pirate_user'@'%';
GRANT CREATE, DROP, ALTER, INDEX ON pirate_content.* TO 'pirate_user'@'localhost';
GRANT CREATE, DROP, ALTER, INDEX ON pirate_content.* TO 'pirate_user'@'172.18.0.1';
GRANT CREATE, DROP, ALTER, INDEX ON pirate_content.* TO 'pirate_user'@'172.%';

FLUSH PRIVILEGES;

SELECT 'User permissions setup completed' as status;