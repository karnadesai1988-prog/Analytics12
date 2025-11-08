# R Territory AI Predictive Insights Engine

**Independent, Platform-Agnostic Territory Management with AI Analytics**

Deploy anywhere - Docker, AWS, Heroku, Digital Ocean, or any VPS. Zero dependency on Emergent platform.

## 🚀 Key Features

### Core Capabilities
- **Circle-Based Territories**: 3km radius geo-fencing instead of polygons
- **Pin-Point Event System**: Add location-specific events with social media showcase
- **AI Predictive Analytics**: Price appreciation predictions (0-25%)
- **Share Links**: Network-based data gathering with live sync
- **Real-Time WebSocket**: Multi-device synchronization
- **Bring Your Own API Key**: Configure OpenAI key via UI
- **100% Independent**: No Emergent dependencies

### Territory System (NEW)
- Click map to select center point
- Automatic 3km radius geo-fence
- Color-coded by appreciation (green=high, red=low)
- Real-time updates across network

### Event Pins (NEW)
- Add pins for events, infrastructure, social posts, issues
- Visible on map with custom markers
- Social media showcase option
- Category-based filtering

### Share Links (NEW)
- Generate shareable URLs for territories
- WiFi network data gathering
- Real-time submission visibility
- 30-day expiration

## 🛠️ Tech Stack

**Backend**: FastAPI + MongoDB + OpenAI (optional) + WebSocket
**Frontend**: React 19 + Leaflet + Shadcn UI + Recharts
**Deployment**: Docker Compose (included)

## 📦 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone <your-repo>
cd r-territory

# Configure environment
cp .env.example .env
# Edit .env and set JWT_SECRET

# Start all services
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
# MongoDB: localhost:27017
```

### Option 2: Manual Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend**
```bash
cd frontend
yarn install
cp .env.example .env
# Set REACT_APP_BACKEND_URL
yarn start
```

**MongoDB**
```bash
# Install and start MongoDB
mongod --dbpath /path/to/data
```

## 🔑 API Key Configuration

### Method 1: UI Configuration (Recommended)
1. Login to application
2. Go to Settings page
3. Enter your OpenAI API key
4. Save configuration

### Method 2: Environment Variable
```bash
# In backend/.env
OPENAI_API_KEY=sk-your-key-here
```

### Get OpenAI API Key
Visit: https://platform.openai.com/api-keys

**Note**: API key is optional. Regex validation works without it.

## 📍 New Territory Features

### Creating Territories
1. Click "Create Territory"
2. Click on map to select center point
3. Auto 3km radius applied
4. Enter name, city, zone
5. Submit - AI calculates appreciation

### Adding Event Pins
1. Click "Add Event Pin"
2. Select territory
3. Click map for exact location
4. Enter title, description, category
5. Toggle social share on/off

### Sharing for Data Gathering
1. Click territory on map
2. Click "Share Link"
3. Copy URL
4. Share on WiFi network
5. Recipients submit data anonymously
6. View real-time submissions

## 🌐 Deployment Options

### AWS EC2
```bash
ssh -i key.pem ubuntu@your-ec2
sudo apt install docker.io docker-compose
git clone <repo>
docker-compose up -d
```

### Heroku
```bash
# Backend
heroku create app-api
heroku addons:create mongolab
git push heroku main

# Frontend
heroku create app-web
heroku config:set REACT_APP_BACKEND_URL=https://app-api.herokuapp.com
git push heroku main
```

### Digital Ocean
1. Create Droplet
2. Install Docker
3. Clone repo
4. Run docker-compose

### Any VPS
Works on any Linux server with:
- Docker 20.10+
- 1GB RAM minimum
- 10GB storage

## 🔒 Security

### Environment Variables
```bash
# Production .env
MONGO_URL=mongodb://your-mongo-host:27017
JWT_SECRET=generate-strong-random-key-here
CORS_ORIGINS=https://yourdomain.com
OPENAI_API_KEY=sk-optional
```

### Production Checklist
- [ ] Strong JWT_SECRET (32+ characters)
- [ ] HTTPS enabled
- [ ] MongoDB authentication
- [ ] CORS restricted to domain
- [ ] Rate limiting configured
- [ ] Regular backups

## 📊 API Endpoints

### Public Endpoints
- `POST /api/data-gathering/public` - Submit data via share link
- `GET /api/share-links/validate/{token}` - Validate share link

### Protected Endpoints (JWT Required)
- `POST /api/territories` - Create territory (3km radius)
- `POST /api/events` - Add event pin
- `POST /api/share-links` - Generate share link
- `POST /api/auth/config-api-key` - Configure OpenAI key
- All other existing endpoints

## 🗺️ Map Features

### Territory Circles
- Center: Latitude/Longitude
- Radius: 3000m (3km) default
- Color: Based on appreciation %
- Click for details popup

### Event Markers
- Red pins for events
- Categories: social, infrastructure, event, issue
- Social media showcase indicator
- Click for event details

### Interaction
- Click map to select location
- Zoom controls
- Legend with appreciation scale
- Real-time updates

## 📱 Pages

1. **Dashboard**: Stats and top territories
2. **Territory Map**: Interactive with circles and pins
3. **Data Gathering**: Form-based collection
4. **Analytics**: Charts and trends
5. **Comments**: AI-validated feedback
6. **Settings**: API key configuration (NEW)

## 🔧 Configuration

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=r_territory_db
CORS_ORIGINS=*
JWT_SECRET=your-secret-key
OPENAI_API_KEY=sk-optional
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 📈 Features Comparison

| Feature | Old | New |
|---------|-----|-----|
| Territory Shape | Polygons | 3km Circles ✓ |
| Location Selection | Manual coordinates | Click map ✓ |
| Event System | None | Pin markers ✓ |
| Data Sharing | None | Share links ✓ |
| API Keys | Emergent only | Bring your own ✓ |
| Deployment | Emergent only | Anywhere ✓ |

## 🚫 Zero Dependencies

✅ No Emergent platform required
✅ No proprietary libraries
✅ Standard OpenAI SDK
✅ Deploy anywhere
✅ Full control over data
✅ Open source stack

## 🧪 Testing

```bash
# Create test user
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User","role":"admin"}'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Create territory (use token from login)
curl -X POST http://localhost:8001/api/territories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Area","city":"Delhi","zone":"Central","center":{"lat":28.6139,"lng":77.2090},"radius":3000,"metrics":{...}}'
```

## 📚 Documentation

- **API Docs**: http://localhost:8001/docs (FastAPI auto-generated)
- **Deployment Guide**: See DEPLOYMENT.md
- **Docker Setup**: docker-compose.yml included

## 🤝 Support

Open source project. Deploy anywhere without restrictions.

---

**Version 2.0 - Platform Independent**
