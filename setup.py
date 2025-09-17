#!/usr/bin/env python3
"""
Studagent Setup Script
Automated setup for local development environment
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


class StudagentSetup:
    """Setup class for Studagent local development environment."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.venv_dir = self.backend_dir / "venv"
        self.is_windows = platform.system() == "Windows"

    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "="*60)
        print(f" {text}")
        print("="*60)

    def print_step(self, step_num, text):
        """Print a formatted step."""
        print(f"\n[{step_num}] {text}")

    def run_command(self, command, cwd=None, shell=False):
        """Run a command and return the result."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                shell=shell,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {command}")
            print(f"Error: {e.stderr}")
            return None

    def check_python_version(self):
        """Check if Python version is compatible."""
        self.print_step("1", "Checking Python version...")
        version = sys.version_info
        if version.major == 3 and version.minor >= 9:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
            return True
        else:
            print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.9+")
            return False

    def check_git(self):
        """Check if Git is installed."""
        self.print_step("2", "Checking Git installation...")
        try:
            result = self.run_command(["git", "--version"])
            if result:
                print(f"✅ {result}")
                return True
        except:
            pass
        print("❌ Git not found. Please install Git first.")
        return False

    def create_virtual_environment(self):
        """Create Python virtual environment."""
        self.print_step("3", "Creating virtual environment...")

        if self.venv_dir.exists():
            print(f"⚠️  Virtual environment already exists at {self.venv_dir}")
            response = input("Remove existing venv and create new one? (y/N): ")
            if response.lower() == 'y':
                shutil.rmtree(self.venv_dir)
            else:
                print("✅ Using existing virtual environment")
                return True

        try:
            self.run_command([sys.executable, "-m", "venv", str(self.venv_dir)])
            print(f"✅ Virtual environment created at {self.venv_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False

    def activate_venv_and_install(self):
        """Activate virtual environment and install dependencies."""
        self.print_step("4", "Installing Python dependencies...")

        # Determine activation script path
        if self.is_windows:
            activate_script = self.venv_dir / "Scripts" / "activate.bat"
            pip_cmd = [str(self.venv_dir / "Scripts" / "pip")]
        else:
            activate_script = self.venv_dir / "bin" / "activate"
            pip_cmd = [str(self.venv_dir / "bin" / "pip")]

        # Upgrade pip first
        try:
            self.run_command(pip_cmd + ["install", "--upgrade", "pip"], cwd=self.backend_dir)
            print("✅ Pip upgraded successfully")
        except:
            print("⚠️  Could not upgrade pip, continuing...")

        # Install requirements
        try:
            self.run_command(pip_cmd + ["install", "-r", "requirements.txt"], cwd=self.backend_dir)
            print("✅ All dependencies installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

    def setup_database(self):
        """Set up the database."""
        self.print_step("5", "Setting up database...")

        # Run seed data script
        seed_script = self.backend_dir / "scripts" / "seed_data.py"

        if seed_script.exists():
            try:
                if self.is_windows:
                    python_cmd = str(self.venv_dir / "Scripts" / "python")
                else:
                    python_cmd = str(self.venv_dir / "bin" / "python")

                self.run_command([python_cmd, str(seed_script)], cwd=self.backend_dir)
                print("✅ Database seeded with sample data")
                return True
            except Exception as e:
                print(f"❌ Failed to seed database: {e}")
                return False
        else:
            print("⚠️  Seed script not found, skipping database setup")
            return True

    def check_redis(self):
        """Check Redis installation and provide setup instructions."""
        self.print_step("6", "Checking Redis setup...")

        try:
            result = self.run_command(["redis-cli", "ping"])
            if "PONG" in result:
                print("✅ Redis is running and accessible")
                return True
        except:
            pass

        print("⚠️  Redis not found or not running")
        print("\nTo install and run Redis:")

        if self.is_windows:
            print("1. Download Redis for Windows from: https://redis.io/download")
            print("2. Extract and run redis-server.exe")
            print("3. Or use Docker: docker run -d -p 6379:6379 redis:7-alpine")
        else:
            print("1. Install Redis:")
            print("   Ubuntu/Debian: sudo apt-get install redis-server")
            print("   macOS: brew install redis")
            print("2. Start Redis: redis-server")
            print("3. Or use Docker: docker run -d -p 6379:6379 redis:7-alpine")

        print("\nFor now, you can run the app without Redis (background tasks will be disabled)")
        return False

    def create_env_file(self):
        """Create .env file from template."""
        self.print_step("7", "Setting up environment configuration...")

        env_template = self.project_root / ".env.example"
        env_file = self.project_root / ".env"

        if env_file.exists():
            print("⚠️  .env file already exists")
            return True

        if env_template.exists():
            shutil.copy(env_template, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your API keys:")
            print("   - OPENROUTER_API_KEY")
            print("   - GEMINI_API_KEY")
            print("   - GROQ_API_KEY")
            print("   - SECRET_KEY (generate a random string)")
            return True
        else:
            print("❌ .env.example template not found")
            return False

    def print_startup_instructions(self):
        """Print instructions for starting the application."""
        self.print_header("🎉 Setup Complete!")

        print("\nTo start the Studagent application:")
        print("\n1. Activate virtual environment:")
        if self.is_windows:
            print(f"   {self.venv_dir}\\Scripts\\activate.bat")
        else:
            print(f"   source {self.venv_dir}/bin/activate")

        print("\n2. Start Redis (if available):")
        print("   redis-server")

        print("\n3. Start the backend server:")
        print("   cd backend")
        if self.is_windows:
            print(f"   {self.venv_dir}\\Scripts\\uvicorn app.main:app --reload")
        else:
            print(f"   {self.venv_dir}/bin/uvicorn app.main:app --reload")

        print("\n4. Open your browser:")
        print("   http://localhost:8000")

        print("\n5. API Documentation:")
        print("   http://localhost:8000/docs")

        print("\n📝 Sample login credentials:")
        print("   Student: alice.student@example.com / password123")
        print("   Mentor:  bob.mentor@example.com / password123")
        print("   Admin:   admin@studagent.com / password123")

        print("\n🔧 Useful commands:")
        print("   • Run tests: pytest tests/")
        print("   • Format code: black backend/")
        print("   • Lint code: ruff check backend/")
        print("   • Seed database: python scripts/seed_data.py")

    def run_setup(self):
        """Run the complete setup process."""
        self.print_header("🚀 Studagent Local Setup")

        print("This script will set up Studagent for local development.")
        print("Make sure you have Python 3.9+ and Git installed.\n")

        # Run setup steps
        steps = [
            self.check_python_version,
            self.check_git,
            self.create_virtual_environment,
            self.activate_venv_and_install,
            self.setup_database,
            self.check_redis,
            self.create_env_file
        ]

        success = True
        for step in steps:
            if not step():
                success = False
                break

        if success:
            self.print_startup_instructions()
        else:
            print("\n❌ Setup failed. Please check the errors above and try again.")
            return 1

        return 0


def main():
    """Main entry point."""
    setup = StudagentSetup()
    return setup.run_setup()


if __name__ == "__main__":
    sys.exit(main())