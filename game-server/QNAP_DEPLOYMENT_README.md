# Planetarion QNAP Deployment Guide

## 🚀 Optimized Deployment for QNAP NAS

This guide provides optimized deployment instructions for running Planetarion on your QNAP NAS with minimal resource usage.

## 📊 Resource Optimization Summary

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| **Total Size** | ~650MB-1GB | ~200-300MB | **60-70%** |
| **Backend** | ~250MB | ~80MB | **68%** |
| **Frontend** | ~400MB | ~50MB | **88%** |
| **Database** | ~150MB | ~100MB | **33%** |
| **RAM Usage** | ~150MB | ~100MB | **33%** |

## 🎯 Hardware Compatibility

**Your QNAP Specs:**
- ✅ **CPU:** Intel Celeron J3455 (4 cores, 1.5GHz) - Perfect for 1-5 users
- ✅ **RAM:** 8GB - More than sufficient
- ✅ **Storage:** 16TB - Plenty of space for game data
- ✅ **Network:** Gigabit Ethernet - Good for local access

**Expected Performance:**
- **CPU Usage:** 5-15% for 1-5 concurrent users
- **RAM Usage:** 100-190MB total
- **Storage:** ~100MB for containers + growing database

## 📋 Prerequisites

### 1. QNAP Setup
- **Container Station** installed (QNAP's Docker management)
- **SSH enabled** on QNAP
- **Admin access** to QNAP

### 2. Local Machine
- **Docker** installed
- **SSH client** configured
- **rsync** for file transfer (optional but recommended)

### 3. Network Access
- QNAP accessible at your configured IP address (default: `192.168.0.133`)
- Ports 5000 (backend) and 3000 (frontend) available

## 🔐 Configuration Setup

### Step 1: Choose Your Configuration Method

**Option A: Environment Variables (Recommended)**
```bash
# Set required environment variables (no defaults provided)
export QNAP_IP="your-qnap-ip"           # Required
export QNAP_USER="your-username"        # Required
export QNAP_PROJECT_DIR="/share/CACHEDEV1_DATA/planetarion"  # Optional
```

**Option B: Local Config File (Alternative)**
```bash
# Copy the example file
cp .qnap-deploy.env.example .qnap-deploy.env

# Edit with your values (QNAP_IP and QNAP_USER are required)
nano .qnap-deploy.env
```

**⚠️ Important:** Scripts will fail if `QNAP_IP` and `QNAP_USER` are not provided. No fallback defaults are used to ensure security.

### Step 2: SSH Setup

**Option 1: Password Authentication**
```bash
# Connect to QNAP
ssh admin@192.168.0.133
# Enter your QNAP admin password
```

**Option 2: SSH Key Authentication (Recommended)**
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096

# Copy public key to QNAP
ssh-copy-id admin@192.168.0.133

# Test connection
ssh admin@192.168.0.133
```

**Option 3: Certificate Authentication**
If you prefer certificate-based authentication, ensure your certificate is properly configured in QNAP's SSH settings.

## 🚀 Quick Deployment

### Step 1: Test Connectivity (Recommended)
Before deploying, test all connectivity and prerequisites:

```bash
cd game-server
./test-qnap-connectivity.sh
```

This will test:
- ✅ Local Docker installation
- ✅ Network connectivity to QNAP
- ✅ SSH access and authentication
- ✅ Docker availability on QNAP
- ✅ Storage space and permissions
- ✅ Port availability

### Step 2: Run the Automated Deployment
```bash
cd game-server
./deploy-to-qnap.sh
```

The script will:
- ✅ **Run connectivity tests automatically**
- ✅ Check prerequisites
- ✅ Setup SSH access
- ✅ Prepare QNAP environment
- ✅ Build optimized images
- ✅ Deploy to QNAP
- ✅ Verify deployment

### Step 3: Access Your Game
Once deployment completes:
- **Frontend:** http://192.168.0.133:3000
- **Backend API:** http://192.168.0.133:5000

## 🔧 Manual Deployment (Alternative)

If you prefer manual control:

### Step 1: Build Optimized Images
```bash
# Build backend
docker build -f src/backend/Dockerfile -t planetarion-backend:qnap src/

# Build frontend
docker build -f src/frontend/Dockerfile -t planetarion-frontend:qnap src/frontend/
```

### Step 2: Transfer to QNAP
```bash
# Copy files to QNAP
scp docker-compose.qnap.yml admin@192.168.0.133:/share/CACHEDEV1_DATA/planetarion/
rsync -avz ./src/ admin@192.168.0.133:/share/CACHEDEV1_DATA/planetarion/src/

# Load images on QNAP
docker save planetarion-backend:qnap | ssh admin@192.168.0.133 "docker load"
docker save planetarion-frontend:qnap | ssh admin@192.168.0.133 "docker load"
```

### Step 3: Start Services on QNAP
```bash
ssh admin@192.168.0.133
cd /share/CACHEDEV1_DATA/planetarion
docker-compose -f docker-compose.qnap.yml up -d --build
```

## 📊 Monitoring & Management

### Check Service Status
```bash
ssh admin@192.168.0.133
cd /share/CACHEDEV1_DATA/planetarion
docker-compose -f docker-compose.qnap.yml ps
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.qnap.yml logs -f

# Specific service
docker-compose -f docker-compose.qnap.yml logs -f backend
docker-compose -f docker-compose.qnap.yml logs -f frontend
docker-compose -f docker-compose.qnap.yml logs -f db
```

### Monitor Resources
```bash
# Container resource usage
docker stats

# QNAP system resources
htop  # Install via QNAP App Center if needed
```

### Restart Services
```bash
docker-compose -f docker-compose.qnap.yml restart
```

### Stop Services
```bash
docker-compose -f docker-compose.qnap.yml down
```

## 🔧 Troubleshooting

### Common Issues

**1. SSH Connection Failed**
```bash
# Check SSH service on QNAP
ssh admin@192.168.0.133
# Enable SSH in QNAP Control Panel > Network & File Services > Telnet/SSH
```

**2. Docker Not Found on QNAP**
- Install **Container Station** from QNAP App Center
- Ensure Container Station is running

**3. Port Already in Use**
```bash
# Check what's using the ports
netstat -tulpn | grep :5000
netstat -tulpn | grep :3000

# Change ports in docker-compose.qnap.yml if needed
```

**4. Permission Denied**
```bash
# Ensure you're using the correct QNAP admin username
# Check file permissions on QNAP storage
```

**5. Build Failures**
```bash
# Clear Docker cache
docker system prune -a

# Check available disk space
df -h
```

### Health Checks

**Test Backend:**
```bash
curl http://192.168.0.133:5000/api/planet
```

**Test Frontend:**
```bash
curl http://192.168.0.133:3000/
```

## 🔄 Updates & Maintenance

### Update the Game
```bash
# On your local machine
cd game-server
./deploy-to-qnap.sh
```

### Backup Database
```bash
ssh admin@192.168.0.133
cd /share/CACHEDEV1_DATA/planetarion
docker-compose -f docker-compose.qnap.yml exec db pg_dump -U planetarion_user planetarion > backup.sql
```

### Restore Database
```bash
docker-compose -f docker-compose.qnap.yml exec -T db psql -U planetarion_user planetarion < backup.sql
```

## 📈 Performance Tuning

### For More Users (6-20)
If you need to support more users, adjust resources in `docker-compose.qnap.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '1.5'    # Increase CPU limit
        memory: 1G     # Increase memory limit
```

### Database Optimization
```yaml
db:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB    # Increase for better performance
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
```

## 🎮 Game Configuration

### Default Admin Account
- **Username:** Create your first account during registration
- **Password:** Set during registration

### Game Settings
Access the game at http://192.168.0.133:3000 and configure:
- User registration
- Planet management
- Fleet operations
- Resource settings

## 📞 Support

If you encounter issues:

1. **Check the logs** using the commands above
2. **Verify network connectivity** to 192.168.0.133
3. **Ensure QNAP has sufficient resources** (check with `htop`)
4. **Test individual services** using health check commands

## 🎯 Success Metrics

**Deployment Success Checklist:**
- ✅ Services running: `docker-compose ps`
- ✅ Backend responding: HTTP 200 at port 5000
- ✅ Frontend loading: HTTP 200 at port 3000
- ✅ Database connected: No connection errors in logs
- ✅ Resources stable: CPU < 20%, RAM < 200MB

**Performance Targets:**
- Page load time: < 2 seconds
- API response time: < 500ms
- Database queries: < 100ms
- Memory usage: < 200MB total

---

**🎉 Your Planetarion server is now optimized and ready for deployment on QNAP!**

Access your game at: **http://192.168.0.133:3000**
