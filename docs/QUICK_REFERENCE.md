# Quick Reference

Quick links and commands for Introlix.

## 📚 Documentation

- [README](../README.md) - Project overview and quick start
- [API Documentation](./API.md) - REST API reference
- [Architecture](./ARCHITECTURE.md) - System design and components
- [Development Guide](./DEVELOPMENT.md) - Contributing and development
- [SearXNG Setup](../README.md#searxng-setup) - Search engine configuration
- [Contributing](./CONTRIBUTING.md) - How to contribute

## 🚀 Quick Start Commands

### Backend

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# Run
uvicorn app:app --reload --port 8000

# Test
pytest
```

### Frontend

```bash
# Setup
cd web
pnpm install

# Run
pnpm dev

# Build
pnpm build

# Test
pnpm test
```

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔧 Configuration

### Environment Variables

```bash
# Copy example
cp .env.example .env

# Required variables
OPEN_ROUTER_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here

SEARCHXNG_HOST=http://localhost:8080
PINECONE_KEY=your_key_here
MONGO_URI=mongodb://localhost:27017/introlix
```

### LLM Provider

Edit `introlix/config.py`:

```python
CLOUD_PROVIDER = "google_ai_studio"  # or "openrouter"
AUTO_MODEL = "gemini-2.5-flash"      # or your preferred model
```

## 🌐 Default URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **SearXNG**: http://localhost:8080

## 📦 Key Dependencies

### Backend
- FastAPI 0.116+
- Python 3.11+
- MongoDB (Motor)
- Pinecone
- PyTorch
- Sentence Transformers

### Frontend
- Next.js 15.5
- React 19
- TypeScript 5
- TanStack Query
- Lexical Editor
- Radix UI

## 🛠️ Common Tasks

### Create Workspace

```bash
curl -X POST http://localhost:8000/workspaces \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workspace", "user_id": "user123"}'
```

### Create Research Desk

```bash
curl -X POST http://localhost:8000/workspace/{workspace_id}/research-desk \
  -H "Content-Type: application/json" \
  -d '{"title": "My Research"}'
```

### Check Backend Health

```bash
curl http://localhost:8000/
```

### View Logs

```bash
# Backend (if using systemd)
sudo journalctl -u introlix-backend -f

# Docker
docker logs -f introlix-backend
```

## 🐛 Debugging

### Backend Issues

```bash
# Check Python version
python --version

# Verify dependencies
pip list

# Test MongoDB connection
mongosh --eval "db.version()"

# Check environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('MONGO_URI'))"
```

### Frontend Issues

```bash
# Check Node version
node --version

# Clear cache
rm -rf web/.next web/node_modules
cd web && pnpm install

# Check build
cd web && pnpm build
```

### SearXNG Issues

```bash
# Test JSON output
curl "http://localhost:8080/search?q=test&format=json"

# Check Docker container
docker ps | grep searxng
docker logs searxng
```

## 📊 Database

### MongoDB Commands

```bash
# Connect
mongosh mongodb://localhost:27017/introlix

# List collections
show collections

# Count documents
db.workspaces.countDocuments()
db.chats.countDocuments()
db.research_desks.countDocuments()

# Find documents
db.workspaces.find().pretty()
```

### Pinecone

```python
from pinecone import Pinecone

pc = Pinecone(api_key="your-key")
index = pc.Index("explored-data-index")

# Check stats
print(index.describe_index_stats())

# Query
results = index.query(vector=[...], top_k=10)
```

## 🔐 Security

### Generate Secret Key

```bash
openssl rand -hex 32
```

### SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d yourdomain.com
```

## 📈 Monitoring

### System Resources

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Network
netstat -tulpn
```

### Application Metrics

```bash
# Request count
grep "POST /workspace" /var/log/nginx/access.log | wc -l

# Error rate
grep "500" /var/log/nginx/access.log | wc -l
```

## 🔄 Updates

### Update Application

```bash
# Pull latest code
git pull origin main

# Update backend
source .venv/bin/activate
pip install -e .
sudo systemctl restart introlix-backend

# Update frontend
cd web
pnpm install
pnpm build
sudo systemctl restart introlix-frontend
```

### Update Dependencies

```bash
# Backend
pip install --upgrade -e .

# Frontend
cd web
pnpm update
```

## 🆘 Getting Help

- **Documentation**: Check the docs folder
- **Issues**: [GitHub Issues](https://github.com/introlix/introlix/issues)
- **Discussions**: [GitHub Discussions](https://github.com/introlix/introlix/discussions)
- **API Docs**: http://localhost:8000/docs

## 📝 License

Apache License 2.0 - See [LICENSE](../LICENSE) file

---

For the most up-to-date information, always refer to the main documentation files.
