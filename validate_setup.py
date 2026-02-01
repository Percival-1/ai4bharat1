#!/usr/bin/env python3
"""
Validation script to check the project setup.
"""

import os
import sys
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and print status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (missing)")
        return False


def check_directory_exists(dir_path: str, description: str) -> bool:
    """Check if a directory exists and print status."""
    if os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (missing)")
        return False


def main():
    """Main validation function."""
    print("🔍 Validating AI-Driven Agri-Civic Intelligence Platform setup...\n")

    all_checks_passed = True

    # Check core project files
    core_files = [
        ("pyproject.toml", "Poetry configuration"),
        ("README.md", "Project documentation"),
        (".env.template", "Environment template"),
        (".gitignore", "Git ignore file"),
        ("docker-compose.yml", "Docker Compose configuration"),
        ("Dockerfile.dev", "Development Dockerfile"),
    ]

    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check application structure
    app_files = [
        ("app/__init__.py", "App package init"),
        ("app/main.py", "FastAPI main application"),
        ("app/config.py", "Configuration management"),
        ("app/api/__init__.py", "API package init"),
        ("app/api/health.py", "Health check endpoints"),
        ("app/core/__init__.py", "Core package init"),
        ("app/core/logging.py", "Logging configuration"),
        ("app/core/middleware.py", "Custom middleware"),
        ("app/models/__init__.py", "Models package init"),
        ("app/services/__init__.py", "Services package init"),
        ("app/utils/__init__.py", "Utils package init"),
    ]

    for file_path, description in app_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check test structure
    test_files = [
        ("tests/__init__.py", "Tests package init"),
        ("tests/test_main.py", "Main application tests"),
        ("tests/test_config.py", "Configuration tests"),
    ]

    for file_path, description in test_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check script files
    script_files = [
        ("scripts/init-db.sql", "Database initialization script"),
        ("scripts/redis.conf", "Redis configuration"),
        ("scripts/setup-dev.sh", "Development setup script (Linux/Mac)"),
        ("scripts/setup-dev.bat", "Development setup script (Windows)"),
    ]

    for file_path, description in script_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    print("\n" + "=" * 60)

    if all_checks_passed:
        print("🎉 All validation checks passed!")
        print("\nNext steps:")
        print("1. Install dependencies: poetry install")
        print("2. Copy .env.template to .env and configure")
        print("3. Start services: docker-compose up -d postgres redis")
        print("4. Run application: poetry run uvicorn app.main:app --reload")
        print("5. Visit http://localhost:8000/docs for API documentation")
        return 0
    else:
        print("❌ Some validation checks failed!")
        print("Please ensure all required files are present.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
