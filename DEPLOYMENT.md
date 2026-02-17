# DigitalOcean Droplet Deployment Guide

## Prerequisites
1. **DigitalOcean Account**: Create a Droplet (Virtual Machine).
   - **Image**: Docker on Ubuntu 22.04 (Marketplace) or standard Ubuntu 22.04.
   - **Size**: Minimum 4GB RAM / 2 vCPU recommended (for AI & Database).
2. **Domain Name** (Optional but recommended): Point `api.yourdomain.com` to your Droplet IP.

---

## Step 1: Server Setup

SSH into your droplet:
```bash
ssh root@your_droplet_ip
```

### Install Docker & Compose (if not using marketplace image)
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository and install
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

## Step 2: Project Deployment

### Option A: Git Clone (Recommended)
1. Generate an SSH key on the server (`ssh-keygen`) and add it to your GitHub Deploy Keys.
2. Clone the repository:
   ```bash
   git clone git@github.com:youruser/microservices-portfolio.git /opt/microservices
   cd /opt/microservices
   ```

### Option B: SCP (Manual Upload)
Upload your local project folder to the server:
```bash
scp -r ./microservices root@your_droplet_ip:/opt/
```

---

## Step 3: Configuration

1. **Environment Variables**:
   Copy the example env file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with production values (API Keys, Database Passwords):
   ```bash
   nano .env
   ```
   *Critical: Change `DB_PASSWORD`, `REDIS_PASSWORD`, and set `GEMINI_API_KEY`.*

2. **Traefik Configuration**:
   Ensure `traefik.yml` or labels in `docker-compose.yml` are set for production. If using a domain, configure Let's Encrypt for HTTPS in Traefik.

---

## Step 4: Launch Services

Start the stack in detached mode:
```bash
docker compose up -d --build
```

Check status:
```bash
docker compose ps
docker compose logs -f
```

---

## Step 5: Data Initialization

1. **Run Migrations**:
   ```bash
   # Business Core (Laravel)
   docker compose exec business-core php artisan migrate --force

   # AI Service (Vector DB Schema)
   # (Managed automatically by app startup, or verify manually)
   ```

2. **Ingest Profile Data**:
   Upload your `cv.pdf` and `profile_data.md` to `ai-service/data/` if not present.
   Run ingestion:
   ```bash
   docker compose exec ai-service python scripts/ingest_cv.py
   ```

---

## Step 6: Security Hardening (UFW)

Enable Firewall to only allow necessary ports:
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Troubleshooting

- **Logs**: `docker compose logs -f [service_name]`
- **Restart**: `docker compose restart [service_name]`
- **Rebuild**: `docker compose up -d --build [service_name]`
