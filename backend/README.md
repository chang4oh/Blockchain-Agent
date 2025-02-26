# Backend

This directory contains the backend code for the Blockchain Agent project.

## Getting Started

1. Choose your preferred backend technology:
   - Node.js with Express
   - Python with Django/Flask
   - Other

2. Set up your environment:
   - Install dependencies
   - Configure environment variables (see `.env.example` in the root directory)
   - Set up your database

3. Implement your API endpoints:
   - Authentication
   - Blockchain data fetching
   - Trading logic
   - User settings

## Structure

The recommended structure for your backend:

```
backend/
├── src/              # Source code
├── tests/            # Test files
├── config/           # Configuration files
└── README.md         # This file
```

## Environment Variables

Make sure to set up the following environment variables in the root `.env` file:

- `BLOCKCHAIN_API_KEY`: Your blockchain API key
- `HUGGINGFACE_API_KEY`: Your Hugging Face API key
- Other API keys and secrets as needed 