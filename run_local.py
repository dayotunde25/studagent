#!/usr/bin/env python3
"""
Local Development Runner for Studagent
Provides easy commands to run the application locally
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class LocalRunner:
    """Local development runner for Studagent."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.venv_dir = self.backend_dir / "venv"
        self.is_windows = platform.system() == "Windows"

    def get_venv_python(self):
        """Get the path to the virtual environment Python executable."""
        if self.is_windows:
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"

    def get_venv_uvicorn(self):
        """Get the path to the virtual environment uvicorn executable."""
        if self.is_windows:
            return self.venv_dir / "Scripts" / "uvicorn.exe"
        else:
            return self.venv_dir / "bin" / "uvicorn"

    def check_venv(self):
        """Check if virtual environment exists and is activated."""
        venv_python = self.get_venv_python()
        if not venv_python.exists():
            print("❌ Virtual environment not found!")
            print("Please run: python setup.py")
            return False
        return True

    def start_backend(self):
        """Start the FastAPI backend server."""
        if not self.check_venv():
            return

        print("🚀 Starting Studagent Backend...")
        print("📍 Backend will be available at: http://localhost:8000")
        print("📖 API Documentation at: http://localhost:8000/docs")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)

        uvicorn_path = self.get_venv_uvicorn()
        os.chdir(self.backend_dir)

        try:
            subprocess.run([
                str(uvicorn_path),
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ], check=True)
        except KeyboardInterrupt:
            print("\n👋 Backend server stopped")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start backend: {e}")

    def run_tests(self):
        """Run the test suite."""
        if not self.check_venv():
            return

        print("🧪 Running tests...")
        venv_python = self.get_venv_python()
        os.chdir(self.backend_dir)

        try:
            subprocess.run([
                str(venv_python), "-m", "pytest",
                "tests/", "-v", "--tb=short"
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed: {e}")

    def seed_database(self):
        """Seed the database with sample data."""
        if not self.check_venv():
            return

        print("🌱 Seeding database with sample data...")
        venv_python = self.get_venv_python()

        try:
            subprocess.run([
                str(venv_python),
                str(self.backend_dir / "scripts" / "seed_data.py")
            ], check=True)
            print("✅ Database seeded successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to seed database: {e}")

    def check_redis(self):
        """Check if Redis is running."""
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and "PONG" in result.stdout:
                print("✅ Redis is running")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass

        print("⚠️  Redis is not running")
        print("To start Redis:")
        if self.is_windows:
            print("  1. Download Redis for Windows")
            print("  2. Run: redis-server.exe")
        else:
            print("  1. Install: sudo apt-get install redis-server")
            print("  2. Start: sudo systemctl start redis-server")
        print("  3. Or use Docker: docker run -d -p 6379:6379 redis:7-alpine")
        return False

    def show_help(self):
        """Show help information."""
        print("🎓 Studagent Local Development Runner")
        print("=" * 40)
        print()
        print("Available commands:")
        print("  python run_local.py backend    - Start the backend server")
        print("  python run_local.py test       - Run the test suite")
        print("  python run_local.py seed       - Seed database with sample data")
        print("  python run_local.py redis      - Check Redis status")
        print("  python run_local.py help       - Show this help")
        print()
        print("Quick start:")
        print("  1. python setup.py              # Initial setup")
        print("  2. python run_local.py backend  # Start development server")
        print()
        print("Sample login credentials:")
        print("  Student: alice.student@example.com / password123")
        print("  Mentor:  bob.mentor@example.com / password123")
        print("  Admin:   admin@studagent.com / password123")

    def main(self):
        """Main entry point."""
        if len(sys.argv) < 2:
            self.show_help()
            return

        command = sys.argv[1].lower()

        if command == "backend":
            self.start_backend()
        elif command == "test":
            self.run_tests()
        elif command == "seed":
            self.seed_database()
        elif command == "redis":
            self.check_redis()
        elif command == "help":
            self.show_help()
        else:
            print(f"❌ Unknown command: {command}")
            self.show_help()


if __name__ == "__main__":
    runner = LocalRunner()
    runner.main()