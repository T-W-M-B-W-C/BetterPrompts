package main

import (
	"database/sql"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

type Migration struct {
	Version     int
	Description string
	UpFile      string
	DownFile    string
	AppliedAt   *time.Time
}

type Migrator struct {
	db           *sql.DB
	upDir        string
	downDir      string
	migrations   []Migration
}

func NewMigrator(dsn, upDir, downDir string) (*Migrator, error) {
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	m := &Migrator{
		db:      db,
		upDir:   upDir,
		downDir: downDir,
	}

	if err := m.createMigrationTable(); err != nil {
		return nil, err
	}

	if err := m.loadMigrations(); err != nil {
		return nil, err
	}

	return m, nil
}

func (m *Migrator) createMigrationTable() error {
	query := `
	CREATE TABLE IF NOT EXISTS public.schema_migrations (
		version INTEGER PRIMARY KEY,
		description VARCHAR(255) NOT NULL,
		applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
		checksum VARCHAR(64)
	)`
	
	_, err := m.db.Exec(query)
	return err
}

func (m *Migrator) loadMigrations() error {
	// Load migration files
	upFiles, err := filepath.Glob(filepath.Join(m.upDir, "*.sql"))
	if err != nil {
		return err
	}

	for _, upFile := range upFiles {
		basename := filepath.Base(upFile)
		parts := strings.SplitN(basename, "_", 2)
		if len(parts) != 2 {
			continue
		}

		version, err := strconv.Atoi(parts[0])
		if err != nil {
			continue
		}

		description := strings.TrimSuffix(parts[1], ".sql")
		description = strings.ReplaceAll(description, "_", " ")

		downFile := filepath.Join(m.downDir, basename)
		if _, err := os.Stat(downFile); os.IsNotExist(err) {
			log.Printf("Warning: No down migration for %s", basename)
			downFile = ""
		}

		m.migrations = append(m.migrations, Migration{
			Version:     version,
			Description: description,
			UpFile:      upFile,
			DownFile:    downFile,
		})
	}

	// Sort migrations by version
	sort.Slice(m.migrations, func(i, j int) bool {
		return m.migrations[i].Version < m.migrations[j].Version
	})

	// Load applied migrations
	rows, err := m.db.Query("SELECT version, applied_at FROM public.schema_migrations")
	if err != nil {
		return err
	}
	defer rows.Close()

	applied := make(map[int]time.Time)
	for rows.Next() {
		var version int
		var appliedAt time.Time
		if err := rows.Scan(&version, &appliedAt); err != nil {
			return err
		}
		applied[version] = appliedAt
	}

	// Mark applied migrations
	for i := range m.migrations {
		if appliedAt, ok := applied[m.migrations[i].Version]; ok {
			m.migrations[i].AppliedAt = &appliedAt
		}
	}

	return nil
}

func (m *Migrator) getCurrentVersion() int {
	var version int
	err := m.db.QueryRow("SELECT COALESCE(MAX(version), 0) FROM public.schema_migrations").Scan(&version)
	if err != nil {
		return 0
	}
	return version
}

func (m *Migrator) runMigration(migration Migration, direction string) error {
	var file string
	if direction == "up" {
		file = migration.UpFile
	} else {
		file = migration.DownFile
		if file == "" {
			return fmt.Errorf("no down migration for version %d", migration.Version)
		}
	}

	content, err := ioutil.ReadFile(file)
	if err != nil {
		return fmt.Errorf("failed to read migration file: %w", err)
	}

	tx, err := m.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	if _, err := tx.Exec(string(content)); err != nil {
		return fmt.Errorf("failed to execute migration: %w", err)
	}

	if direction == "up" {
		_, err = tx.Exec("INSERT INTO public.schema_migrations (version, description) VALUES ($1, $2) ON CONFLICT (version) DO NOTHING",
			migration.Version, migration.Description)
	} else {
		_, err = tx.Exec("DELETE FROM public.schema_migrations WHERE version = $1", migration.Version)
	}

	if err != nil {
		return fmt.Errorf("failed to update migration table: %w", err)
	}

	return tx.Commit()
}

func (m *Migrator) Up(targetVersion int) error {
	currentVersion := m.getCurrentVersion()
	fmt.Printf("Current version: %d\n", currentVersion)

	applied := 0
	for _, migration := range m.migrations {
		if migration.Version <= currentVersion {
			continue
		}
		if targetVersion > 0 && migration.Version > targetVersion {
			break
		}

		fmt.Printf("Applying migration %d: %s\n", migration.Version, migration.Description)
		if err := m.runMigration(migration, "up"); err != nil {
			return fmt.Errorf("migration %d failed: %w", migration.Version, err)
		}
		applied++
		fmt.Printf("✓ Migration %d applied successfully\n", migration.Version)
	}

	if applied == 0 {
		fmt.Println("No new migrations to apply")
	} else {
		fmt.Printf("Applied %d migration(s)\n", applied)
	}

	return nil
}

func (m *Migrator) Down(targetVersion int) error {
	currentVersion := m.getCurrentVersion()
	fmt.Printf("Current version: %d\n", currentVersion)

	if currentVersion == 0 {
		fmt.Println("No migrations to rollback")
		return nil
	}

	rolledBack := 0
	for i := len(m.migrations) - 1; i >= 0; i-- {
		migration := m.migrations[i]
		if migration.Version > currentVersion {
			continue
		}
		if migration.Version <= targetVersion {
			break
		}

		fmt.Printf("Rolling back migration %d: %s\n", migration.Version, migration.Description)
		if err := m.runMigration(migration, "down"); err != nil {
			return fmt.Errorf("rollback %d failed: %w", migration.Version, err)
		}
		rolledBack++
		fmt.Printf("✓ Migration %d rolled back successfully\n", migration.Version)
	}

	if rolledBack == 0 {
		fmt.Println("No migrations to rollback")
	} else {
		fmt.Printf("Rolled back %d migration(s)\n", rolledBack)
	}

	return nil
}

func (m *Migrator) Status() {
	fmt.Println("Migration Status")
	fmt.Println("================")
	fmt.Printf("Current version: %d\n\n", m.getCurrentVersion())

	fmt.Println("Migrations:")
	for _, migration := range m.migrations {
		status := "pending"
		if migration.AppliedAt != nil {
			status = fmt.Sprintf("applied at %s", migration.AppliedAt.Format("2006-01-02 15:04:05"))
		}
		fmt.Printf("  %03d - %-40s [%s]\n", migration.Version, migration.Description, status)
	}
}

func (m *Migrator) Close() error {
	return m.db.Close()
}

func main() {
	var (
		host     = flag.String("host", getEnv("DB_HOST", "localhost"), "Database host")
		port     = flag.String("port", getEnv("DB_PORT", "5432"), "Database port")
		dbname   = flag.String("dbname", getEnv("DB_NAME", "betterprompts"), "Database name")
		user     = flag.String("user", getEnv("DB_USER", "betterprompts"), "Database user")
		password = flag.String("password", getEnv("DB_PASSWORD", "betterprompts"), "Database password")
		sslmode  = flag.String("sslmode", getEnv("DB_SSLMODE", "disable"), "SSL mode")
		command  = flag.String("cmd", "status", "Command: up, down, or status")
		version  = flag.Int("version", 0, "Target version (0 means all)")
	)
	flag.Parse()

	// Build DSN
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		*host, *port, *user, *password, *dbname, *sslmode)

	// Get migration directories
	execPath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}
	scriptsDir := filepath.Dir(execPath)
	migrationsDir := filepath.Dir(scriptsDir)
	upDir := filepath.Join(migrationsDir, "up")
	downDir := filepath.Join(migrationsDir, "down")

	// Create migrator
	migrator, err := NewMigrator(dsn, upDir, downDir)
	if err != nil {
		log.Fatal(err)
	}
	defer migrator.Close()

	// Execute command
	switch *command {
	case "up":
		if err := migrator.Up(*version); err != nil {
			log.Fatal(err)
		}
	case "down":
		if err := migrator.Down(*version); err != nil {
			log.Fatal(err)
		}
	case "status":
		migrator.Status()
	default:
		fmt.Println("Usage: migrate -cmd=[up|down|status] [-version=N]")
		flag.PrintDefaults()
		os.Exit(1)
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}