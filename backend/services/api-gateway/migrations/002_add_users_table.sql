-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    roles TEXT[] DEFAULT ARRAY['user'],
    is_active BOOLEAN DEFAULT true,
    is_email_verified BOOLEAN DEFAULT false,
    email_verify_token TEXT,
    password_reset_token TEXT,
    password_reset_expiry TIMESTAMP,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON users(LOWER(email));
CREATE INDEX idx_users_username ON users(LOWER(username));
CREATE INDEX idx_users_roles ON users USING GIN(roles);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create user_sessions table for refresh tokens
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Create api_keys table for developer access
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash TEXT NOT NULL,
    permissions TEXT[],
    rate_limit INTEGER DEFAULT 1000,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);

-- Add user_id to prompt_history table
ALTER TABLE prompt_history 
ADD COLUMN IF NOT EXISTS user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_prompt_history_user_id ON prompt_history(user_id);

-- Insert default roles
INSERT INTO roles (id, name, description, permissions) VALUES
    ('1', 'user', 'Basic user role', ARRAY['prompt:read:own', 'prompt:write:own', 'prompt:delete:own', 'profile:read:own', 'profile:write:own']),
    ('2', 'developer', 'Developer role with API access', ARRAY['prompt:read:own', 'prompt:write:own', 'prompt:delete:own', 'prompt:read:public', 'profile:read:own', 'profile:write:own', 'api:access:full', 'metrics:read:own']),
    ('3', 'admin', 'Administrator role with full access', ARRAY['prompt:read:all', 'prompt:write:all', 'prompt:delete:all', 'user:read:all', 'user:write:all', 'user:delete:all', 'profile:read:all', 'profile:write:all', 'api:access:full', 'metrics:read:all', 'system:config:all'])
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (id, name, resource, action, description) VALUES
    ('1', 'prompt:read:own', 'prompt', 'read:own', 'Read own prompts'),
    ('2', 'prompt:write:own', 'prompt', 'write:own', 'Create and update own prompts'),
    ('3', 'prompt:delete:own', 'prompt', 'delete:own', 'Delete own prompts'),
    ('4', 'prompt:read:all', 'prompt', 'read:all', 'Read all prompts'),
    ('5', 'prompt:write:all', 'prompt', 'write:all', 'Create and update all prompts'),
    ('6', 'prompt:delete:all', 'prompt', 'delete:all', 'Delete all prompts'),
    ('7', 'prompt:read:public', 'prompt', 'read:public', 'Read public prompts'),
    ('8', 'user:read:all', 'user', 'read:all', 'Read all users'),
    ('9', 'user:write:all', 'user', 'write:all', 'Create and update all users'),
    ('10', 'user:delete:all', 'user', 'delete:all', 'Delete all users'),
    ('11', 'profile:read:own', 'profile', 'read:own', 'Read own profile'),
    ('12', 'profile:write:own', 'profile', 'write:own', 'Update own profile'),
    ('13', 'profile:read:all', 'profile', 'read:all', 'Read all profiles'),
    ('14', 'profile:write:all', 'profile', 'write:all', 'Update all profiles'),
    ('15', 'api:access:full', 'api', 'access:full', 'Full API access'),
    ('16', 'metrics:read:own', 'metrics', 'read:own', 'Read own metrics'),
    ('17', 'metrics:read:all', 'metrics', 'read:all', 'Read all metrics'),
    ('18', 'system:config:all', 'system', 'config:all', 'Configure system settings')
ON CONFLICT (name) DO NOTHING;