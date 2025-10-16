# Smart Deploy Engine

An intelligent automated deployment system for LLM-powered code generation and GitHub Pages hosting.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GitHub Personal Access Token
- AIPipe API Token

### Installation

1. **Environment Setup**
   ```bash
   python -m venv deployment_env
   source deployment_env/bin/activate  # On Windows: deployment_env\\Scripts\\activate
   ```

2. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Verification**
   ```bash
   python verify_services.py
   ```

5. **Launch**
   ```bash
   uvicorn core_engine.server:app --reload --host 0.0.0.0 --port 8000
   ```

## 📡 API Endpoints

### Deployment Endpoint
**POST** `/deploy-endpoint`

Accepts JSON payload for automated code generation and deployment:
```json
{
  "email": "user@example.com",
  "secret": "your_secret_key",
  "task": "project-identifier",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Create a web application that...",
  "checks": ["validation criteria"],
  "evaluation_url": "https://eval.example.com/notify",
  "attachments": [{"name": "file.csv", "url": "data:text/csv;base64,..."}]
}
```

### System Health
**GET** `/health`

Returns system operational status.

## 🏗️ Architecture

### Core Components
- **`core_engine/server.py`** - Main FastAPI application
- **`core_engine/intelligent_generator.py`** - AI-powered code generation
- **`core_engine/repository_manager.py`** - GitHub repository operations
- **`core_engine/evaluation_notifier.py`** - Evaluation endpoint communication

### Key Features
- ✅ Automated repository creation and management
- ✅ AI-powered application generation using AIPipe
- ✅ GitHub Pages auto-configuration
- ✅ Binary and text file handling
- ✅ Duplicate request detection
- ✅ Retry logic with exponential backoff
- ✅ MIT license auto-generation
- ✅ Multi-round deployment support

## 🔧 Configuration

### Environment Variables
```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_USERNAME=your_github_username
USER_SECRET=your_unique_secret
AIPIPE_TOKEN=your_aipipe_token_here
```

### Deployment Modes
- **Round 1**: Fresh repository creation and initial deployment
- **Round 2+**: Enhancement and updates to existing repositories

## 📝 Usage Examples

### Basic Deployment
```bash
curl -X POST http://localhost:8000/deploy-endpoint \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "developer@example.com",
    "secret": "your_secret",
    "task": "weather-app-v1",
    "round": 1,
    "brief": "Create a weather dashboard with current conditions",
    "evaluation_url": "https://eval.example.com/notify"
  }'
```

### Enhancement Deployment
For subsequent rounds, the system automatically enhances existing code based on new requirements.

## 🛡️ Security

- Secure secret-based authentication
- No sensitive data in git history
- Automatic MIT license inclusion
- Environment-based configuration

## 📊 Monitoring

The system provides comprehensive logging for:
- Deployment progress tracking
- GitHub API interactions
- AI generation status
- Evaluation endpoint notifications

## 🔄 Workflow

1. **Request Reception** - Validate and queue deployment request
2. **Asset Processing** - Decode and store attachments
3. **AI Generation** - Create application code and documentation
4. **Repository Management** - Create/update GitHub repository
5. **Pages Configuration** - Enable GitHub Pages hosting
6. **Notification** - Inform evaluation endpoint of completion

## 📈 Performance

- Non-blocking background processing
- Efficient caching for duplicate requests
- Optimized GitHub API usage
- Intelligent retry mechanisms

## 🐛 Troubleshooting

### Common Issues
- **Authentication Errors**: Verify GitHub token permissions
- **AI Generation Failures**: Check AIPipe token and service status
- **Pages Not Loading**: Ensure repository is public and Pages are enabled

### Debug Mode
```bash
uvicorn core_engine.server:app --reload --log-level debug
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

This is an automated deployment system. For modifications, ensure all tests pass and security requirements are met.


