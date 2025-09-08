# 🏴‍☠️ Pirate Content Bot

Enhanced Telegram bot for content requests with advanced features.

## 🚀 CI/CD Pipeline

This project uses GitHub Actions for automated testing and deployment:

### Pipeline Steps:
1. **Testing** - Runs comprehensive tests with MySQL and Redis
2. **Building** - Builds Docker image if tests pass
3. **Deployment** - Automatically deploys to production server

### Required Secrets:
Set these in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

```
DOCKER_USERNAME=your_docker_hub_username
DOCKER_PASSWORD=your_docker_hub_password
SERVER_HOST=your_server_ip
SERVER_USER=your_server_username
SERVER_SSH_KEY=your_private_ssh_key (recommended)
SERVER_PASSWORD=your_server_password (alternative to SSH key)
```

### Deployment Process:
1. Push to `master` branch
2. GitHub Actions runs tests automatically
3. If tests pass → Docker image is built and pushed
4. Production server pulls new image and restarts services

## 🧪 Testing Locally

```bash
# Run specific tests
cd pirate_content_bot
DB_HOST=localhost PYTHONPATH=. python tests/test_specific_requests.py
DB_HOST=localhost PYTHONPATH=. python test_commands.py
DB_HOST=localhost PYTHONPATH=. python tests/test_admin_commands.py

# Run all tests
pytest
```

## 🐳 Docker Commands

```bash
# Build locally
docker-compose build --no-cache

# Run locally
docker-compose up -d

# Stop local containers (when production is running)
docker-compose down

# View logs
docker-compose logs -f
```

## 🔧 Environment Variables

Key environment variables needed:

```env
BOT_TOKEN=your_telegram_bot_token
DB_HOST=database_host
DB_USER=database_user  
DB_PASSWORD=database_password
ADMIN_IDS=comma_separated_admin_user_ids
```

## 📊 Features

- Advanced request detection and analysis
- Admin panel with analytics
- Search functionality
- Broadcast messaging
- User management
- Request fulfillment tracking

---

🤖 *Automated CI/CD powered by GitHub Actions*