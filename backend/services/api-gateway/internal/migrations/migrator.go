package migrations

import (
	"context"
	"database/sql"
	"embed"
	"fmt"
	"log"
	"sort"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

//go:embed sql/*.sql
var migrationFiles embed.FS

// Migration represents a database migration
type Migration struct {
	Version     int
	Name        string
	Description string
	SQL         string
	Rollback    string
}

// Migrator handles database migrations
type Migrator struct {
	db         *sql.DB
	migrations []Migration
}

// NewMigrator creates a new migrator instance
func NewMigrator(db *sql.DB) (*Migrator, error) {
	m := &Migrator{
		db:         db,
		migrations: []Migration{},
	}

	// Create migrations table if not exists
	if err := m.createMigrationTable(); err != nil {
		return nil, fmt.Errorf("failed to create migration table: %w", err)
	}

	// Load migrations from embedded files
	if err := m.loadMigrations(); err != nil {
		return nil, fmt.Errorf("failed to load migrations: %w", err)
	}

	return m, nil
}

// createMigrationTable creates the schema_migrations table
func (m *Migrator) createMigrationTable() error {
	query := `
		CREATE TABLE IF NOT EXISTS public.schema_migrations (
			version INTEGER PRIMARY KEY,
			name VARCHAR(255),
			applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
		)`

	_, err := m.db.Exec(query)
	return err
}

// loadMigrations loads migration files from embedded filesystem
func (m *Migrator) loadMigrations() error {
	entries, err := migrationFiles.ReadDir("sql")
	if err != nil {
		return err
	}

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".sql") {
			continue
		}

		// Parse version from filename (e.g., 001_initial_schema.sql)
		parts := strings.Split(entry.Name(), "_")
		if len(parts) < 2 {
			continue
		}

		version, err := strconv.Atoi(strings.TrimPrefix(parts[0], "0"))
		if err != nil {
			continue
		}

		// Read migration SQL
		content, err := migrationFiles.ReadFile("sql/" + entry.Name())
		if err != nil {
			return fmt.Errorf("failed to read migration %s: %w", entry.Name(), err)
		}

		// Check for rollback file
		rollbackName := fmt.Sprintf("rollback_%03d.sql", version)
		rollbackContent, _ := migrationFiles.ReadFile("sql/" + rollbackName)

		migration := Migration{
			Version:  version,
			Name:     strings.TrimSuffix(entry.Name(), ".sql"),
			SQL:      string(content),
			Rollback: string(rollbackContent),
		}

		// Extract description from SQL comments
		lines := strings.Split(migration.SQL, "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "-- Description:") {
				migration.Description = strings.TrimSpace(strings.TrimPrefix(line, "-- Description:"))
				break
			}
		}

		m.migrations = append(m.migrations, migration)
	}

	// Sort migrations by version
	sort.Slice(m.migrations, func(i, j int) bool {
		return m.migrations[i].Version < m.migrations[j].Version
	})

	return nil
}

// GetCurrentVersion returns the current migration version
func (m *Migrator) GetCurrentVersion() (int, error) {
	var version int
	query := `SELECT COALESCE(MAX(version), 0) FROM public.schema_migrations`
	
	err := m.db.QueryRow(query).Scan(&version)
	if err != nil {
		return 0, err
	}

	return version, nil
}

// GetAppliedMigrations returns list of applied migrations
func (m *Migrator) GetAppliedMigrations() ([]AppliedMigration, error) {
	query := `
		SELECT version, name, applied_at 
		FROM public.schema_migrations 
		ORDER BY version`

	rows, err := m.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var applied []AppliedMigration
	for rows.Next() {
		var am AppliedMigration
		err := rows.Scan(&am.Version, &am.Name, &am.AppliedAt)
		if err != nil {
			return nil, err
		}
		applied = append(applied, am)
	}

	return applied, rows.Err()
}

// Up runs all pending migrations
func (m *Migrator) Up(ctx context.Context) error {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}

	pendingCount := 0
	for _, migration := range m.migrations {
		if migration.Version <= currentVersion {
			continue
		}

		pendingCount++
		if err := m.runMigration(ctx, migration); err != nil {
			return fmt.Errorf("failed to run migration %d: %w", migration.Version, err)
		}
	}

	if pendingCount == 0 {
		log.Println("No pending migrations")
	} else {
		log.Printf("Applied %d migration(s)", pendingCount)
	}

	return nil
}

// UpTo runs migrations up to a specific version
func (m *Migrator) UpTo(ctx context.Context, targetVersion int) error {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}

	if targetVersion <= currentVersion {
		return fmt.Errorf("target version %d must be greater than current version %d", 
			targetVersion, currentVersion)
	}

	for _, migration := range m.migrations {
		if migration.Version <= currentVersion || migration.Version > targetVersion {
			continue
		}

		if err := m.runMigration(ctx, migration); err != nil {
			return fmt.Errorf("failed to run migration %d: %w", migration.Version, err)
		}
	}

	return nil
}

// Down rolls back the last migration
func (m *Migrator) Down(ctx context.Context) error {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}

	if currentVersion == 0 {
		return fmt.Errorf("no migrations to rollback")
	}

	// Find the migration to rollback
	var migration *Migration
	for i := range m.migrations {
		if m.migrations[i].Version == currentVersion {
			migration = &m.migrations[i]
			break
		}
	}

	if migration == nil {
		return fmt.Errorf("migration %d not found", currentVersion)
	}

	if migration.Rollback == "" {
		return fmt.Errorf("no rollback script for migration %d", currentVersion)
	}

	return m.rollbackMigration(ctx, *migration)
}

// DownTo rolls back to a specific version
func (m *Migrator) DownTo(ctx context.Context, targetVersion int) error {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return fmt.Errorf("failed to get current version: %w", err)
	}

	if targetVersion >= currentVersion {
		return fmt.Errorf("target version %d must be less than current version %d", 
			targetVersion, currentVersion)
	}

	// Rollback in reverse order
	for v := currentVersion; v > targetVersion; v-- {
		// Find migration
		var migration *Migration
		for i := range m.migrations {
			if m.migrations[i].Version == v {
				migration = &m.migrations[i]
				break
			}
		}

		if migration == nil {
			return fmt.Errorf("migration %d not found", v)
		}

		if migration.Rollback == "" {
			return fmt.Errorf("no rollback script for migration %d", v)
		}

		if err := m.rollbackMigration(ctx, *migration); err != nil {
			return fmt.Errorf("failed to rollback migration %d: %w", v, err)
		}
	}

	return nil
}

// runMigration executes a single migration
func (m *Migrator) runMigration(ctx context.Context, migration Migration) error {
	log.Printf("Running migration %d: %s", migration.Version, migration.Name)

	// Start transaction
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Execute migration SQL
	if _, err := tx.ExecContext(ctx, migration.SQL); err != nil {
		return fmt.Errorf("failed to execute migration SQL: %w", err)
	}

	// Record migration
	query := `
		INSERT INTO public.schema_migrations (version, name, applied_at)
		VALUES ($1, $2, $3)`
	
	if _, err := tx.ExecContext(ctx, query, migration.Version, migration.Name, time.Now()); err != nil {
		return fmt.Errorf("failed to record migration: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit migration: %w", err)
	}

	log.Printf("✅ Migration %d applied successfully", migration.Version)
	return nil
}

// rollbackMigration executes a migration rollback
func (m *Migrator) rollbackMigration(ctx context.Context, migration Migration) error {
	log.Printf("Rolling back migration %d: %s", migration.Version, migration.Name)

	// Start transaction
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Execute rollback SQL
	if _, err := tx.ExecContext(ctx, migration.Rollback); err != nil {
		return fmt.Errorf("failed to execute rollback SQL: %w", err)
	}

	// Remove migration record
	query := `DELETE FROM public.schema_migrations WHERE version = $1`
	
	if _, err := tx.ExecContext(ctx, query, migration.Version); err != nil {
		return fmt.Errorf("failed to remove migration record: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit rollback: %w", err)
	}

	log.Printf("✅ Migration %d rolled back successfully", migration.Version)
	return nil
}

// Status returns the current migration status
func (m *Migrator) Status() (*Status, error) {
	currentVersion, err := m.GetCurrentVersion()
	if err != nil {
		return nil, err
	}

	applied, err := m.GetAppliedMigrations()
	if err != nil {
		return nil, err
	}

	var pending []Migration
	for _, migration := range m.migrations {
		if migration.Version > currentVersion {
			pending = append(pending, migration)
		}
	}

	return &Status{
		CurrentVersion:     currentVersion,
		AvailableVersion:   m.getLatestVersion(),
		AppliedMigrations:  applied,
		PendingMigrations:  pending,
		TotalMigrations:    len(m.migrations),
	}, nil
}

// getLatestVersion returns the latest available migration version
func (m *Migrator) getLatestVersion() int {
	if len(m.migrations) == 0 {
		return 0
	}
	return m.migrations[len(m.migrations)-1].Version
}

// AppliedMigration represents an applied migration
type AppliedMigration struct {
	Version   int
	Name      string
	AppliedAt time.Time
}

// Status represents the migration status
type Status struct {
	CurrentVersion     int
	AvailableVersion   int
	AppliedMigrations  []AppliedMigration
	PendingMigrations  []Migration
	TotalMigrations    int
}