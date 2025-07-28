-- Create test users for Phase 4 E2E tests
-- Password for all test users: Test123!@#

-- Power user
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified, tier)
VALUES (
  'power',
  'power@example.com',
  '$2a$10$ZxW6Tlvn6H9J6Kx.BmxCIOJ8N5EO0h6i6PWBMhGFaCLBQR6wm5Ojm',
  'Power',
  'User',
  true,
  true,
  'pro'
) ON CONFLICT (email) DO NOTHING;

-- New user
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified, tier)
VALUES (
  'newuser',
  'new@example.com',
  '$2a$10$ZxW6Tlvn6H9J6Kx.BmxCIOJ8N5EO0h6i6PWBMhGFaCLBQR6wm5Ojm',
  'New',
  'User',
  true,
  true,
  'free'
) ON CONFLICT (email) DO NOTHING;