#!/usr/bin/env python3
"""
Generate bcrypt password hashes for database seeding
"""

import sys
import bcrypt
import argparse


def generate_hash(password: str, rounds: int = 10) -> str:
    """
    Generate a bcrypt hash for the given password
    
    Args:
        password: The password to hash
        rounds: The number of rounds for bcrypt (default: 10)
    
    Returns:
        The bcrypt hash as a string
    """
    # Convert to bytes if string
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds)
    hash_bytes = bcrypt.hashpw(password, salt)
    
    return hash_bytes.decode('utf-8')


def verify_hash(password: str, hash_str: str) -> bool:
    """
    Verify a password against a bcrypt hash
    
    Args:
        password: The password to verify
        hash_str: The bcrypt hash string
    
    Returns:
        True if the password matches, False otherwise
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    if isinstance(hash_str, str):
        hash_str = hash_str.encode('utf-8')
    
    return bcrypt.checkpw(password, hash_str)


def main():
    parser = argparse.ArgumentParser(description='Generate bcrypt password hashes')
    parser.add_argument('password', nargs='?', help='Password to hash (will prompt if not provided)')
    parser.add_argument('-r', '--rounds', type=int, default=10, help='Number of rounds (default: 10)')
    parser.add_argument('-v', '--verify', help='Verify password against this hash')
    parser.add_argument('-b', '--batch', action='store_true', help='Generate hashes for common test passwords')
    
    args = parser.parse_args()
    
    if args.batch:
        # Generate hashes for common test passwords
        test_passwords = [
            ('TestPassword123!', 'Default test user password'),
            ('AdminPassword123!', 'Admin user password'),
            ('DeveloperKey123!', 'Developer API key'),
            ('SecureToken456!', 'Secure token example'),
        ]
        
        print("Generating bcrypt hashes for test passwords...")
        print("=" * 60)
        
        for password, description in test_passwords:
            hash_str = generate_hash(password, args.rounds)
            print(f"\n{description}:")
            print(f"Password: {password}")
            print(f"Hash: {hash_str}")
            print(f"SQL: '$2a${args.rounds}${hash_str[7:]}'")
        
        print("\n" + "=" * 60)
        print("⚠️  WARNING: These are for development only!")
        print("Never use these passwords in production!")
        
    elif args.verify:
        # Verify mode
        if not args.password:
            import getpass
            password = getpass.getpass("Enter password to verify: ")
        else:
            password = args.password
        
        is_valid = verify_hash(password, args.verify)
        
        if is_valid:
            print("✅ Password is valid!")
            sys.exit(0)
        else:
            print("❌ Password is invalid!")
            sys.exit(1)
    
    else:
        # Generate single hash
        if not args.password:
            import getpass
            password = getpass.getpass("Enter password to hash: ")
            confirm = getpass.getpass("Confirm password: ")
            
            if password != confirm:
                print("❌ Passwords do not match!")
                sys.exit(1)
        else:
            password = args.password
        
        hash_str = generate_hash(password, args.rounds)
        
        print(f"\nPassword: {password}")
        print(f"Hash: {hash_str}")
        print(f"\nFor SQL insert:")
        print(f"'{hash_str}'")
        
        # Verify the hash works
        if verify_hash(password, hash_str):
            print("\n✅ Hash verified successfully!")
        else:
            print("\n❌ Hash verification failed!")
            sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)