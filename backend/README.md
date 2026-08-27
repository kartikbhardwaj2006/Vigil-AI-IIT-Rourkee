# VIGIL Backend

Privacy-Preserving Intelligent Surveillance Decision-Support System

## Requirements

- Python 3.10+
- MySQL 8.0+
- Redis (optional, for real-time features)

## Quick Start

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit: http://localhost:8000/docs
