# SearXNG Setup Guide

This guide provides detailed instructions for setting up SearXNG as the search engine for Introlix.

## Table of Contents

- [What is SearXNG?](#what-is-searxng)
- [Why SearXNG?](#why-searxng)
- [Docker Setup (Recommended)](#docker-setup-recommended)
- [Manual Installation](#manual-installation)
- [Configuration for Introlix](#configuration-for-introlix)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## What is SearXNG?

SearXNG is a free, privacy-respecting metasearch engine that aggregates results from multiple search engines without tracking users. It's a fork of the original Searx project with additional features and improvements.

**Key Features:**
- Privacy-focused (no tracking, no profiling)
- Aggregates results from 70+ search engines
- Self-hosted (full control over your data)
- JSON API support (required for Introlix)
- Highly configurable

---

## Why SearXNG?

Introlix uses SearXNG for several reasons:

1. **Privacy**: No user tracking or data collection
2. **Self-hosted**: Complete control over search infrastructure
3. **JSON API**: Easy integration with backend services
4. **Aggregation**: Better results from multiple sources
5. **Free**: No API costs or rate limits

---

## Docker Setup (Recommended)

Docker is the easiest way to run SearXNG. This method works on Linux, macOS, and Windows.

### Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually included with Docker Desktop)

### Step 1: Create Docker Compose File

In your Introlix project root, create `docker-compose.yml`:

```yaml
version: '3.7'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped
    networks:
      - searxng-network

networks:
  searxng-network:
    driver: bridge
```

### Step 2: Create SearXNG Configuration Directory

```bash
mkdir -p searxng
```

### Step 3: Create Settings File

Create `searxng/settings.yml`:

```yaml
# SearXNG Configuration for Introlix
use_default_settings: true

general:
  # Instance name shown in the UI
  instance_name: "Introlix Search"
  
  # Privacy settings
  privacypolicy_url: false
  donation_url: false
  contact_url: false
  
  # Enable autocomplete
  autocomplete: ""

server:
  # Secret key for session encryption (change this!)
  secret_key: "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_AT_LEAST_32_CHARS"
  
  # Disable rate limiting for local use
  limiter: false
  
  # Enable image proxy for privacy
  image_proxy: true
  
  # HTTP settings
  bind_address: "0.0.0.0"
  port: 8080

search:
  # Safe search level (0=off, 1=moderate, 2=strict)
  safe_search: 0
  
  # Autocomplete provider
  autocomplete: ""
  
  # Default language
  default_lang: "en"
  
  # IMPORTANT: Enable JSON format for Introlix
  formats:
    - html
    - json
    - csv
    - rss

ui:
  # Use static file hashing
  static_use_hash: true
  
  # Default theme
  default_theme: simple
  
  # Default locale
  default_locale: "en"
  
  # Results per page
  results_on_new_tab: false
  
  # Infinite scroll
  infinite_scroll: false

# Enable specific search engines
engines:
  # General search
  - name: google
    disabled: false
    weight: 1.0
    
  - name: duckduckgo
    disabled: false
    weight: 1.0
    
  - name: bing
    disabled: false
    weight: 0.8
    
  # Academic search
  - name: google scholar
    disabled: false
    weight: 1.0
    
  - name: arxiv
    disabled: false
    weight: 1.0
    
  - name: pubmed
    disabled: false
    weight: 1.0
    
  # Reference
  - name: wikipedia
    disabled: false
    weight: 1.0
    
  # News
  - name: google news
    disabled: false
    weight: 0.8
    
  # Code
  - name: github
    disabled: false
    weight: 1.0
    
  - name: stackoverflow
    disabled: false
    weight: 1.0

# Outgoing request settings
outgoing:
  # Request timeout
  request_timeout: 10.0
  
  # Max request timeout
  max_request_timeout: 15.0
  
  # Enable HTTP/2
  enable_http2: true
  
  # User agent
  useragent_suffix: "Introlix Bot"
  
  # Proxies (optional)
  # proxies:
  #   http: http://proxy:8080
  #   https: http://proxy:8080
```

### Step 4: Generate Secret Key

Generate a secure secret key:

```bash
# Linux/macOS
openssl rand -hex 32

# Or use Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Replace `CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_AT_LEAST_32_CHARS` in `settings.yml` with the generated key.

### Step 5: Start SearXNG

```bash
docker-compose up -d
```

Check if it's running:

```bash
docker ps | grep searxng
```

View logs:

```bash
docker logs searxng
```

### Step 6: Verify Installation

Open your browser and visit:
- **Web UI**: http://localhost:8080
- **JSON API Test**: http://localhost:8080/search?q=test&format=json

You should see search results in JSON format.

### Step 7: Update Introlix Configuration

In your `.env` file:

```env
SEARCHXNG_HOST=http://localhost:8080
```

---

## Manual Installation

If you prefer not to use Docker, you can install SearXNG manually.

### Prerequisites

- Python 3.8+
- pip
- virtualenv
- git

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y \
    python3-dev python3-venv python3-pip \
    git build-essential libxslt-dev \
    zlib1g-dev libffi-dev libssl-dev \
    shellcheck
```

**macOS:**
```bash
brew install python git
```

### Step 2: Clone SearXNG

```bash
cd /opt
sudo git clone https://github.com/searxng/searxng.git
cd searxng
```

### Step 3: Create Virtual Environment

```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -U pip setuptools wheel
sudo venv/bin/pip install -e .
```

### Step 4: Create Configuration

```bash
sudo mkdir -p /etc/searxng
sudo cp searx/settings.yml /etc/searxng/settings.yml
```

Edit `/etc/searxng/settings.yml` with the configuration from Step 3 of Docker setup.

### Step 5: Create Systemd Service

Create `/etc/systemd/system/searxng.service`:

```ini
[Unit]
Description=SearXNG
After=network.target

[Service]
Type=simple
User=searxng
Group=searxng
WorkingDirectory=/opt/searxng
Environment="SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml"
ExecStart=/opt/searxng/venv/bin/python /opt/searxng/searx/webapp.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 6: Create User and Set Permissions

```bash
sudo useradd -r -s /bin/false searxng
sudo chown -R searxng:searxng /opt/searxng
sudo chown -R searxng:searxng /etc/searxng
```

### Step 7: Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable searxng
sudo systemctl start searxng
```

Check status:

```bash
sudo systemctl status searxng
```

---

## Configuration for Introlix

### Required Settings

For Introlix to work properly, ensure these settings are in `settings.yml`:

```yaml
search:
  formats:
    - html
    - json  # REQUIRED: Must include JSON
```

### Recommended Settings

```yaml
server:
  limiter: false  # Disable rate limiting for local use

outgoing:
  request_timeout: 10.0  # Reasonable timeout
  max_request_timeout: 15.0
```

### Optional: Custom Search Engines

You can customize which search engines to use:

```yaml
engines:
  # Disable engines you don't want
  - name: yahoo
    disabled: true
    
  # Adjust weights (higher = more priority)
  - name: google
    weight: 1.5
    
  # Add custom engines
  - name: my_custom_engine
    engine: xpath
    search_url: https://example.com/search?q={query}
    # ... more configuration
```

---

## Testing

### Test Web Interface

1. Open http://localhost:8080
2. Enter a search query
3. Verify results appear

### Test JSON API

```bash
# Basic search
curl "http://localhost:8080/search?q=artificial+intelligence&format=json"

# With specific engines
curl "http://localhost:8080/search?q=python&format=json&engines=google,duckduckgo"

# With language
curl "http://localhost:8080/search?q=test&format=json&language=en"
```

### Test from Python

```python
import requests

response = requests.get(
    "http://localhost:8080/search",
    params={
        "q": "machine learning",
        "format": "json"
    }
)

data = response.json()
print(f"Found {len(data.get('results', []))} results")
for result in data.get('results', [])[:5]:
    print(f"- {result['title']}: {result['url']}")
```

### Test with Introlix

1. Start Introlix backend
2. Create a new chat
3. Ask a question that requires search
4. Check backend logs for search requests

---

## Troubleshooting

### SearXNG Not Starting

**Check Docker logs:**
```bash
docker logs searxng
```

**Common issues:**
- Invalid `settings.yml` syntax (use YAML validator)
- Port 8080 already in use (change port in docker-compose.yml)
- Missing secret key

### JSON Format Not Working

**Verify settings.yml includes JSON:**
```yaml
search:
  formats:
    - html
    - json
```

**Restart SearXNG:**
```bash
docker-compose restart searxng
```

### No Search Results

**Check enabled engines:**
```bash
curl "http://localhost:8080/config" | jq '.engines'
```

**Test specific engine:**
```bash
curl "http://localhost:8080/search?q=test&format=json&engines=google"
```

### Slow Search Results

**Reduce timeout:**
```yaml
outgoing:
  request_timeout: 5.0
  max_request_timeout: 10.0
```

**Disable slow engines:**
```yaml
engines:
  - name: slow_engine
    disabled: true
```

### Connection Refused from Introlix

**If using Docker:**
- Use `http://localhost:8080` (not `http://searxng:8080`)
- Ensure SearXNG container is running: `docker ps`

**If using systemd:**
- Check service status: `sudo systemctl status searxng`
- Check firewall: `sudo ufw status`

### Rate Limiting Issues

**Disable limiter for local use:**
```yaml
server:
  limiter: false
```

---

## Advanced Configuration

### Using HTTPS

For production, use a reverse proxy like Nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name search.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using Tor for Privacy

Add Tor proxy to `settings.yml`:

```yaml
outgoing:
  proxies:
    http: socks5://127.0.0.1:9050
    https: socks5://127.0.0.1:9050
```

### Custom Branding

```yaml
general:
  instance_name: "My Custom Search"
  
ui:
  default_theme: simple
  # Add custom CSS
  custom_css: |
    #search_logo { display: none; }
```

---

## Performance Optimization

### Enable Redis Caching

Add Redis to `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:alpine
    container_name: searxng-redis
    networks:
      - searxng-network
      
  searxng:
    # ... existing config
    environment:
      - SEARXNG_REDIS_URL=redis://redis:6379/0
```

Update `settings.yml`:

```yaml
redis:
  url: redis://redis:6379/0
```

### Optimize Engine Selection

Only enable engines you need:

```yaml
engines:
  # Fast, reliable engines
  - name: duckduckgo
    disabled: false
    
  # Disable slow or unreliable engines
  - name: qwant
    disabled: true
```

---

## Security Best Practices

1. **Change the secret key** - Never use the default
2. **Use HTTPS in production** - Protect user queries
3. **Enable rate limiting** - Prevent abuse (if public)
4. **Keep SearXNG updated** - Regular security updates
5. **Monitor logs** - Watch for suspicious activity

---

## Additional Resources

- [SearXNG Documentation](https://docs.searxng.org/)
- [SearXNG GitHub](https://github.com/searxng/searxng)
- [Available Engines](https://docs.searxng.org/admin/engines/configured_engines.html)
- [Settings Reference](https://docs.searxng.org/admin/settings/index.html)

---

## Getting Help

If you encounter issues:

1. Check SearXNG logs: `docker logs searxng`
2. Visit [SearXNG Issues](https://github.com/searxng/searxng/issues)
3. Ask in [Introlix Discussions](https://github.com/introlix/introlix-research/discussions)
