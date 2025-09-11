-- Load timezone data
-- This script loads timezone data to fix timezone warnings

-- Set default timezone
SET GLOBAL time_zone = '+00:00';
SET time_zone = '+00:00';

-- Basic timezone support setup
-- Insert some common timezones to prevent warnings
INSERT IGNORE INTO mysql.time_zone (Use_leap_seconds) VALUES ('N');
INSERT IGNORE INTO mysql.time_zone_name (Name, Time_zone_id) VALUES ('UTC', 1);
INSERT IGNORE INTO mysql.time_zone_name (Name, Time_zone_id) VALUES ('GMT', 1);

-- Set system timezone variables
SET GLOBAL system_time_zone = 'UTC';

-- Reload timezone tables
FLUSH TABLES;

SELECT 'Timezone initialization completed' as status;