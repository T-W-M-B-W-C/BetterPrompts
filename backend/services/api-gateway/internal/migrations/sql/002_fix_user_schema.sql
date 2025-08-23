-- Add missing columns
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255);
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255);
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS roles TEXT[] DEFAULT '{"user"}';
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);

-- Set default roles based on tier (if roles is null)
UPDATE auth.users SET roles = 
  CASE 
    WHEN tier = 'enterprise' THEN ARRAY['user', 'premium', 'enterprise']
    WHEN tier = 'pro' THEN ARRAY['user', 'premium']
    ELSE ARRAY['user']
  END
WHERE roles IS NULL;
