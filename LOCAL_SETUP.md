# Studagent Local Setup Guide

This guide will help you set up and run Studagent on your local machine using Python virtual environment (no Docker required).

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9 or higher
- Git
- Redis (optional, for background tasks)

### 2. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd studagent

# Run automated setup
python setup.py
```

### 3. Configure Environment
Edit the `.env` file that was created and add your API keys:
```bash
# Required API Keys (get from respective providers)
OPENROUTER_API_KEY=your-openrouter-key-here
GEMINI_API_KEY=your-gemini-key-here
GROQ_API_KEY=your-groq-key-here

# Generate a secure random string for this
SECRET_KEY=your-secure-random-string-here
```

### 4. Start the Application
```bash
# Start the backend server
python run_local.py backend
```

### 5. Access the Application
- **Web Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 📝 Sample Accounts

After running the setup, you can log in with these sample accounts:

| Role | Email | Password |
|------|-------|----------|
| Student | alice.student@example.com | password123 |
| Mentor | bob.mentor@example.com | password123 |
| Admin | admin@studagent.com | password123 |

## 🛠️ Available Commands

### Setup Commands
```bash
# Initial setup (creates venv, installs deps, sets up DB)
python setup.py

# Seed database with sample data
python run_local.py seed
```

### Development Commands
```bash
# Start backend server
python run_local.py backend

# Run tests
python run_local.py test

# Check Redis status
python run_local.py redis
```

### Manual Commands
```bash
# Activate virtual environment
cd backend
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start server manually
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests manually
pytest tests/ -v

# Format code
black .
isort .
ruff check . --fix
```

## 🔧 Redis Setup (Optional)

Redis is used for background task processing. Without it, some features will work but background tasks won't be processed.

### Windows
1. Download Redis for Windows from https://redis.io/download
2. Extract the files
3. Run `redis-server.exe`

### macOS
```bash
brew install redis
redis-server
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### Docker (Alternative)
```bash
docker run -d -p 6379:6379 --name studagent-redis redis:7-alpine
```

## 🧪 Testing

```bash
# Run all tests
python run_local.py test

# Run specific test file
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pytest tests/unit/test_models.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 📁 Project Structure

```
studagent/
├── backend/                 # FastAPI backend
│   ├── app/                # Main application
│   │   ├── routers/        # API route handlers
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utility functions
│   │   ├── static/         # Static files (CSS, JS)
│   │   └── templates/      # Jinja2 templates
│   ├── tests/              # Test suite
│   ├── scripts/            # Utility scripts
│   └── requirements.txt    # Python dependencies
├── docs/                   # Documentation
├── scripts/                # Deployment scripts
├── .env                    # Environment variables
├── setup.py               # Setup script
├── run_local.py          # Local runner script
└── README.md              # Main documentation
```

## 🔑 API Keys Setup

### OpenRouter API Key
1. Go to https://openrouter.ai/
2. Sign up for an account
3. Generate an API key
4. Add it to your `.env` file

### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Add it to your `.env` file

### Groq API Key
1. Go to https://console.groq.com/
2. Sign up and create an API key
3. Add it to your `.env` file

## 🚨 Troubleshooting

### Common Issues

**1. Virtual environment not found**
```bash
# Delete old venv and run setup again
rm -rf backend/venv
python setup.py
```

**2. Port 8000 already in use**
```bash
# Use a different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**3. Database errors**
```bash
# Reset database
rm backend/studagent.db
python run_local.py seed
```

**4. Import errors**
```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Getting Help

- Check the main README.md for detailed documentation
- Review the API documentation at http://localhost:8000/docs
- Check the test output for specific error messages
- Ensure all required API keys are properly configured

## 🎯 Next Steps

Once you have the application running locally:

1. **Explore the Features**: Try uploading a document and generating flashcards
2. **Test the APIs**: Use the interactive API documentation
3. **Run the Tests**: Ensure everything is working correctly
4. **Customize**: Modify the code to add your own features
5. **Deploy**: Use the deployment scripts for production deployment

## 📞 Support

- **Documentation**: Check the `docs/` folder for detailed guides
- **API Reference**: Available at `/docs` when the server is running
- **Issues**: Check the test output for specific error messages
- **Logs**: Check the console output for debugging information

Happy coding! 🚀