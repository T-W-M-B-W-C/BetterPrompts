-- Rollback Migration: 002_roles_permissions.sql
-- Description: Remove RBAC tables and functions
-- Author: Backend Team
-- Date: 2024-01-20

-- Drop triggers
DROP TRIGGER IF EXISTS sync_user_roles_on_update ON auth.users;
DROP TRIGGER IF EXISTS update_roles_updated_at ON auth.roles;

-- Drop functions
DROP FUNCTION IF EXISTS auth.sync_user_roles();
DROP FUNCTION IF EXISTS auth.get_user_permissions(UUID);
DROP FUNCTION IF EXISTS auth.user_has_permission(UUID, VARCHAR, VARCHAR);

-- Drop audit table
DROP TABLE IF EXISTS auth.permission_audit_log;

-- Drop junction tables
DROP TABLE IF EXISTS auth.user_roles;
DROP TABLE IF EXISTS auth.role_permissions;

-- Drop core tables
DROP TABLE IF EXISTS auth.permissions;
DROP TABLE IF EXISTS auth.roles;

-- Remove migration record
DELETE FROM public.schema_migrations WHERE version = 2;