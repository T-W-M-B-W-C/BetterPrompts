-- Migration: 002_roles_permissions.sql
-- Description: Add RBAC (Role-Based Access Control) tables
-- Author: Backend Team
-- Date: 2024-01-20

-- =====================================================
-- ROLES AND PERMISSIONS TABLES
-- =====================================================

-- Roles table
CREATE TABLE IF NOT EXISTS auth.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false NOT NULL, -- System roles cannot be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Permissions table
CREATE TABLE IF NOT EXISTS auth.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT permissions_resource_action_unique UNIQUE (resource, action)
);

-- Role permissions junction table
CREATE TABLE IF NOT EXISTS auth.role_permissions (
    role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    granted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    PRIMARY KEY (role_id, permission_id)
);

-- User role assignments (many-to-many)
CREATE TABLE IF NOT EXISTS auth.user_roles (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, role_id)
);

-- =====================================================
-- AUDIT TABLES
-- =====================================================

-- Audit log for permission changes
CREATE TABLE IF NOT EXISTS auth.permission_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- grant, revoke, create, delete
    target_type VARCHAR(50) NOT NULL, -- role, permission, user_role
    target_id UUID NOT NULL,
    details JSONB DEFAULT '{}' NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Role indexes
CREATE INDEX idx_roles_name ON auth.roles(name);
CREATE INDEX idx_roles_is_system ON auth.roles(is_system);

-- Permission indexes
CREATE INDEX idx_permissions_resource ON auth.permissions(resource);
CREATE INDEX idx_permissions_action ON auth.permissions(action);

-- Junction table indexes
CREATE INDEX idx_role_permissions_role_id ON auth.role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON auth.role_permissions(permission_id);
CREATE INDEX idx_user_roles_user_id ON auth.user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON auth.user_roles(role_id);

-- Audit log indexes
CREATE INDEX idx_permission_audit_user_id ON auth.permission_audit_log(user_id);
CREATE INDEX idx_permission_audit_created_at ON auth.permission_audit_log(created_at DESC);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update trigger for roles
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON auth.roles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to check if a user has a specific permission
CREATE OR REPLACE FUNCTION auth.user_has_permission(
    p_user_id UUID,
    p_resource VARCHAR,
    p_action VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_has_permission BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM auth.user_roles ur
        JOIN auth.role_permissions rp ON ur.role_id = rp.role_id
        JOIN auth.permissions p ON rp.permission_id = p.id
        WHERE ur.user_id = p_user_id
          AND p.resource = p_resource
          AND p.action = p_action
    ) INTO v_has_permission;
    
    RETURN v_has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get all permissions for a user
CREATE OR REPLACE FUNCTION auth.get_user_permissions(p_user_id UUID)
RETURNS TABLE (
    permission_name VARCHAR,
    resource VARCHAR,
    action VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        p.name AS permission_name,
        p.resource,
        p.action
    FROM auth.user_roles ur
    JOIN auth.role_permissions rp ON ur.role_id = rp.role_id
    JOIN auth.permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = p_user_id
    ORDER BY p.resource, p.action;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to sync user roles with the roles array in users table
CREATE OR REPLACE FUNCTION auth.sync_user_roles()
RETURNS TRIGGER AS $$
DECLARE
    v_role_id UUID;
    v_role_name TEXT;
BEGIN
    -- Remove roles that are no longer in the array
    DELETE FROM auth.user_roles
    WHERE user_id = NEW.id
      AND role_id NOT IN (
          SELECT r.id
          FROM auth.roles r
          WHERE r.name = ANY(NEW.roles)
      );
    
    -- Add new roles from the array
    FOREACH v_role_name IN ARRAY NEW.roles
    LOOP
        SELECT id INTO v_role_id
        FROM auth.roles
        WHERE name = v_role_name;
        
        IF v_role_id IS NOT NULL THEN
            INSERT INTO auth.user_roles (user_id, role_id)
            VALUES (NEW.id, v_role_id)
            ON CONFLICT (user_id, role_id) DO NOTHING;
        END IF;
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to sync user roles when users.roles array changes
CREATE TRIGGER sync_user_roles_on_update
AFTER INSERT OR UPDATE OF roles ON auth.users
FOR EACH ROW EXECUTE FUNCTION auth.sync_user_roles();

-- =====================================================
-- INITIAL DATA - System Roles
-- =====================================================

-- Insert system roles
INSERT INTO auth.roles (name, description, is_system) VALUES
    ('user', 'Standard user with basic access', true),
    ('developer', 'Developer with API access and extended features', true),
    ('admin', 'Administrator with full system access', true)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- INITIAL DATA - Permissions
-- =====================================================

-- Prompt permissions
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('prompt:read:own', 'prompt', 'read:own', 'Read own prompts'),
    ('prompt:write:own', 'prompt', 'write:own', 'Create and update own prompts'),
    ('prompt:delete:own', 'prompt', 'delete:own', 'Delete own prompts'),
    ('prompt:read:public', 'prompt', 'read:public', 'Read public prompts'),
    ('prompt:read:all', 'prompt', 'read:all', 'Read all prompts'),
    ('prompt:write:all', 'prompt', 'write:all', 'Create and update any prompts'),
    ('prompt:delete:all', 'prompt', 'delete:all', 'Delete any prompts')
ON CONFLICT (name) DO NOTHING;

-- User/Profile permissions
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('profile:read:own', 'profile', 'read:own', 'Read own profile'),
    ('profile:write:own', 'profile', 'write:own', 'Update own profile'),
    ('profile:read:all', 'profile', 'read:all', 'Read all profiles'),
    ('profile:write:all', 'profile', 'write:all', 'Update any profile'),
    ('user:read:all', 'user', 'read:all', 'View all users'),
    ('user:write:all', 'user', 'write:all', 'Create and update users'),
    ('user:delete:all', 'user', 'delete:all', 'Delete users')
ON CONFLICT (name) DO NOTHING;

-- API permissions
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('api:access:basic', 'api', 'access:basic', 'Basic API access'),
    ('api:access:full', 'api', 'access:full', 'Full API access with higher limits')
ON CONFLICT (name) DO NOTHING;

-- Analytics permissions
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('metrics:read:own', 'metrics', 'read:own', 'View own usage metrics'),
    ('metrics:read:all', 'metrics', 'read:all', 'View all system metrics')
ON CONFLICT (name) DO NOTHING;

-- System permissions
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('system:config:read', 'system', 'config:read', 'Read system configuration'),
    ('system:config:write', 'system', 'config:write', 'Modify system configuration'),
    ('system:config:all', 'system', 'config:all', 'Full system configuration access')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- ASSIGN PERMISSIONS TO ROLES
-- =====================================================

-- User role permissions
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM auth.roles r
CROSS JOIN auth.permissions p
WHERE r.name = 'user'
  AND p.name IN (
      'prompt:read:own',
      'prompt:write:own',
      'prompt:delete:own',
      'profile:read:own',
      'profile:write:own',
      'api:access:basic'
  )
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Developer role permissions
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM auth.roles r
CROSS JOIN auth.permissions p
WHERE r.name = 'developer'
  AND p.name IN (
      'prompt:read:own',
      'prompt:write:own',
      'prompt:delete:own',
      'prompt:read:public',
      'profile:read:own',
      'profile:write:own',
      'api:access:full',
      'metrics:read:own'
  )
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Admin role permissions (all permissions)
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM auth.roles r
CROSS JOIN auth.permissions p
WHERE r.name = 'admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- =====================================================
-- MIGRATE EXISTING USER ROLES
-- =====================================================

-- Populate user_roles table based on existing users.roles array
INSERT INTO auth.user_roles (user_id, role_id)
SELECT DISTINCT
    u.id AS user_id,
    r.id AS role_id
FROM auth.users u
CROSS JOIN LATERAL unnest(u.roles) AS role_name
JOIN auth.roles r ON r.name = role_name
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Record migration
INSERT INTO public.schema_migrations (version, description, checksum)
VALUES (2, 'Roles and permissions', md5('002_roles_permissions'))
ON CONFLICT (version) DO NOTHING;