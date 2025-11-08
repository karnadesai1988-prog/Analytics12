from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import re
import numpy as np
from openai import AsyncOpenAI
import json
import secrets
from collections import defaultdict

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

openai_client = None
if os.environ.get('OPENAI_API_KEY'):
    openai_client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

app = FastAPI(title="R Territory AI Engine - Ahmedabad")
api_router = APIRouter(prefix="/api")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# ==================== MODELS ====================

class UserRole:
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"
    COMMUNITY_HEAD = "community_head"
    MONITOR = "monitor"  # View only
    PARTNER = "partner"  # Comment access
    CHANNEL_PARTNER = "channel_partner"  # Pin and data submission

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = UserRole.VIEWER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str
    openai_api_key: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TerritoryMetrics(BaseModel):
    investments: float = 0
    buildings: int = 0
    populationDensity: float = 0
    qualityOfProject: float = 0
    govtInfra: float = 0
    livabilityIndex: float = 0
    airPollutionIndex: float = 0
    roads: float = 0
    crimeRate: float = 0

class TerritoryRestrictions(BaseModel):
    rentFamilyOnly: bool = False
    pgAllowed: bool = True

class AIInsights(BaseModel):
    appreciationPercent: float = 0
    demandPressure: float = 0
    confidenceScore: float = 0
    aiSuggestions: List[str] = []

class Territory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    city: str
    zone: str
    center: Dict[str, float]
    radius: float = 5000
    metrics: TerritoryMetrics
    restrictions: TerritoryRestrictions
    aiInsights: AIInsights
    liveAnalytics: Optional[Dict[str, Any]] = None
    createdBy: str
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TerritoryCreate(BaseModel):
    name: str
    city: str
    zone: str
    center: Dict[str, float]
    radius: float = 5000
    metrics: TerritoryMetrics = Field(default_factory=TerritoryMetrics)
    restrictions: TerritoryRestrictions = Field(default_factory=TerritoryRestrictions)

class TerritoryUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zone: Optional[str] = None
    center: Optional[Dict[str, float]] = None
    radius: Optional[float] = None
    metrics: Optional[TerritoryMetrics] = None
    restrictions: Optional[TerritoryRestrictions] = None

class Pin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location: Dict[str, float]
    type: List[str]
    label: str
    description: Optional[str] = None
    address: Optional[str] = None
    hasGeofence: bool = False
    geofenceRadius: float = 1000
    territoryId: Optional[str] = None
    projectId: Optional[str] = None
    eventId: Optional[str] = None
    aiInsights: Optional[Dict[str, Any]] = None
    createdBy: str
    userName: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PinCreate(BaseModel):
    location: Dict[str, float]
    type: List[str]
    label: str
    description: Optional[str] = None
    address: Optional[str] = None
    hasGeofence: bool = False
    geofenceRadius: float = 1000
    territoryId: Optional[str] = None
    projectId: Optional[str] = None
    eventId: Optional[str] = None
    generateAIInsights: bool = False

class PinUpdate(BaseModel):
    location: Optional[Dict[str, float]] = None
    type: Optional[List[str]] = None
    label: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    hasGeofence: Optional[bool] = None
    geofenceRadius: Optional[float] = None
    territoryId: Optional[str] = None
    projectId: Optional[str] = None
    eventId: Optional[str] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    location: Dict[str, float]
    territoryId: Optional[str] = None
    status: str = "active"
    budget: Optional[float] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    aiRecommendations: List[str] = []
    createdBy: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    name: str
    description: str
    location: Dict[str, float]
    territoryId: Optional[str] = None
    status: str = "active"
    budget: Optional[float] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    generateAIRecommendations: bool = False

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    location: Dict[str, float]
    territoryId: Optional[str] = None
    projectId: Optional[str] = None
    eventDate: datetime
    category: str
    attendeesEstimate: Optional[int] = None
    aiPredictions: Optional[Dict[str, Any]] = None
    createdBy: str
    userName: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventCreate(BaseModel):
    title: str
    description: str
    location: Dict[str, float]
    territoryId: Optional[str] = None
    projectId: Optional[str] = None
    eventDate: datetime
    category: str
    attendeesEstimate: Optional[int] = None
    generateAIPredictions: bool = False

class CommentCreate(BaseModel):
    territoryId: str
    text: str
    useAI: bool = False
    apiKey: Optional[str] = None

class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    userId: str
    userName: str
    text: str
    validationStatus: str
    validationReason: Optional[str] = None
    sentiment: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DataGatheringForm(BaseModel):
    territoryId: str
    data: Dict[str, Any]
    submittedBy: str
    shareToken: Optional[str] = None

class DataGathering(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    data: Dict[str, Any]
    submittedBy: str
    shareToken: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ShareLink(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    territoryId: str
    createdBy: str
    expiresAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30))
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MetricsHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    metrics: TerritoryMetrics
    aiInsights: AIInsights
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class APIKeyConfig(BaseModel):
    openai_api_key: Optional[str] = None

class AIAnalysisRequest(BaseModel):
    entityType: str
    entityId: str
    analysisType: str

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    return verify_token(token)

def check_permission(user_role: str, required_roles: List[str]):
    if user_role not in required_roles:
        raise HTTPException(status_code=403, detail=f"Access denied. Required roles: {', '.join(required_roles)}")

async def analyze_gathered_data(territory_id: str) -> Dict[str, Any]:
    """Analyze all gathered data for a territory and generate live analytics"""
    try:
        gathered_data = await db.data_gathering.find({"territoryId": territory_id}, {"_id": 0}).to_list(1000)
        
        if not gathered_data:
            return {
                "totalSubmissions": 0,
                "avgPropertyValue": 0,
                "avgRentPrice": 0,
                "avgOccupancyRate": 0,
                "avgMaintenanceCost": 0,
                "tenantDistribution": {},
                "submissionTrend": "No data",
                "dataQuality": "N/A"
            }
        
        property_values = []
        rent_prices = []
        occupancy_rates = []
        maintenance_costs = []
        tenant_types = defaultdict(int)
        
        for entry in gathered_data:
            data = entry.get('data', {})
            
            if data.get('propertyValue'):
                try:
                    property_values.append(float(data['propertyValue']))
                except:
                    pass
            
            if data.get('rentPrice'):
                try:
                    rent_prices.append(float(data['rentPrice']))
                except:
                    pass
            
            if data.get('occupancyRate'):
                try:
                    occupancy_rates.append(float(data['occupancyRate']))
                except:
                    pass
            
            if data.get('maintenanceCost'):
                try:
                    maintenance_costs.append(float(data['maintenanceCost']))
                except:
                    pass
            
            if data.get('tenantType'):
                tenant_types[data['tenantType']] += 1
        
        analytics = {
            "totalSubmissions": len(gathered_data),
            "avgPropertyValue": round(sum(property_values) / len(property_values), 2) if property_values else 0,
            "avgRentPrice": round(sum(rent_prices) / len(rent_prices), 2) if rent_prices else 0,
            "avgOccupancyRate": round(sum(occupancy_rates) / len(occupancy_rates), 2) if occupancy_rates else 0,
            "avgMaintenanceCost": round(sum(maintenance_costs) / len(maintenance_costs), 2) if maintenance_costs else 0,
            "tenantDistribution": dict(tenant_types),
            "submissionTrend": "Increasing" if len(gathered_data) > 10 else "Growing",
            "dataQuality": "High" if len(gathered_data) > 20 else "Medium" if len(gathered_data) > 5 else "Low",
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
        
        return analytics
    except Exception as e:
        logging.error(f"Error analyzing data: {e}")
        return {"error": str(e)}

async def update_territory_analytics(territory_id: str):
    """Update territory with live analytics based on gathered data"""
    try:
        analytics = await analyze_gathered_data(territory_id)
        
        await db.territories.update_one(
            {"id": territory_id},
            {"$set": {"liveAnalytics": analytics}}
        )
        
        territory = await db.territories.find_one({"id": territory_id}, {"_id": 0})
        
        await manager.broadcast(json.dumps({
            "type": "analytics_updated",
            "territoryId": territory_id,
            "analytics": analytics
        }))
        
        return analytics
    except Exception as e:
        logging.error(f"Error updating analytics: {e}")
        return None

def predict_appreciation(metrics: TerritoryMetrics) -> AIInsights:
    try:
        investment_factor = min(np.log10(metrics.investments + 1) / 2, 1.0)
        
        appreciation = (
            investment_factor * 5 +
            (metrics.livabilityIndex / 10) * 5 +
            (metrics.govtInfra / 10) * 4 +
            (metrics.qualityOfProject / 10) * 4 +
            (metrics.roads / 10) * 3 +
            (1 - metrics.crimeRate / 10) * 2 +
            (1 - metrics.airPollutionIndex / 10) * 2
        )
        
        demand_pressure = min((
            (metrics.populationDensity / 1000) * 30 +
            (metrics.buildings / 200) * 30 +
            investment_factor * 40
        ), 100)
        
        confidence = min(0.70 + (metrics.qualityOfProject / 50) + (metrics.govtInfra / 50), 0.95)
        
        suggestions = []
        if metrics.livabilityIndex < 6:
            suggestions.append("Improve livability index through better amenities")
        if metrics.roads < 7:
            suggestions.append("Road infrastructure needs enhancement")
        if metrics.crimeRate > 5:
            suggestions.append("Focus on safety and security measures")
        if metrics.airPollutionIndex > 6:
            suggestions.append("Implement pollution control initiatives")
        
        return AIInsights(
            appreciationPercent=round(max(0, min(appreciation, 25)), 2),
            demandPressure=round(max(0, demand_pressure), 2),
            confidenceScore=round(confidence, 2),
            aiSuggestions=suggestions
        )
    except Exception as e:
        logging.error(f"Error in predict_appreciation: {e}")
        return AIInsights(appreciationPercent=0, demandPressure=0, confidenceScore=0.5, aiSuggestions=[])

async def generate_pin_ai_insights(pin_data: dict, api_key: str = None) -> Dict:
    try:
        key = api_key or os.environ.get('OPENAI_API_KEY')
        if not key:
            return {"analysis": "AI insights unavailable", "recommendations": []}
        
        client = AsyncOpenAI(api_key=key)
        
        prompt = f"""Analyze this location pin data and provide business insights:
        Type: {', '.join(pin_data.get('type', []))}
        Label: {pin_data.get('label', '')}
        Description: {pin_data.get('description', 'N/A')}
        
        Provide:
        1. Strategic importance (1-2 sentences)
        2. 3 actionable recommendations
        3. Risk assessment
        
        Format as JSON with keys: importance, recommendations (array), risks"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"AI insights error: {e}")
        return {"analysis": "Error generating insights", "recommendations": []}

def validate_comment_regex(text: str) -> Dict:
    banned_patterns = [
        r'spam', r'fake', r'free\s+money', r'abuse', r'offensive',
        r'click\s+here', r'buy\s+now', r'urgent', r'winner'
    ]
    
    for pattern in banned_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"label": "flagged", "reason": f"Matched banned pattern: {pattern}", "sentiment": "negative"}
    
    return {"label": "valid", "reason": "No violations detected", "sentiment": "neutral"}

async def validate_comment_ai(text: str, api_key: str) -> Dict:
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze comment for spam/abuse and provide sentiment. Respond with JSON: {status: 'VALID' or 'FLAGGED', reason: string, sentiment: 'positive'/'neutral'/'negative'}"},
                {"role": "user", "content": text}
            ],
            max_tokens=100
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "label": "flagged" if result.get("status") == "FLAGGED" else "valid",
            "reason": result.get("reason", "AI validation completed"),
            "sentiment": result.get("sentiment", "neutral")
        }
    except Exception as e:
        logging.error(f"AI validation error: {e}")
        return {"label": "valid", "reason": "AI validation unavailable", "sentiment": "neutral"}

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserRegister):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(email=user_data.email, name=user_data.name, role=user_data.role)
    doc = user.model_dump()
    doc['password_hash'] = hash_password(user_data.password)
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    return user

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['email'], user['role'])
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "openai_api_key": user.get('openai_api_key')
        }
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: Dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/auth/config-api-key")
async def configure_api_key(config: APIKeyConfig, current_user: Dict = Depends(get_current_user)):
    await db.users.update_one({"id": current_user['user_id']}, {"$set": {"openai_api_key": config.openai_api_key}})
    return {"message": "API key configured successfully"}

# ==================== TERRITORY ROUTES ====================

@api_router.post("/territories", response_model=Territory)
async def create_territory(territory_data: TerritoryCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.COMMUNITY_HEAD])
    
    ai_insights = predict_appreciation(territory_data.metrics)
    territory = Territory(
        name=territory_data.name, city=territory_data.city, zone=territory_data.zone,
        center=territory_data.center, radius=territory_data.radius,
        metrics=territory_data.metrics, restrictions=territory_data.restrictions,
        aiInsights=ai_insights, liveAnalytics=None, createdBy=current_user['user_id']
    )
    doc = territory.model_dump()
    doc['updatedAt'] = doc['updatedAt'].isoformat()
    await db.territories.insert_one(doc)
    
    history = MetricsHistory(territoryId=territory.id, metrics=territory.metrics, aiInsights=ai_insights)
    history_doc = history.model_dump()
    history_doc['timestamp'] = history_doc['timestamp'].isoformat()
    await db.metrics_history.insert_one(history_doc)
    
    broadcast_data = {k: v for k, v in doc.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "territory_created", "data": broadcast_data}))
    return territory

@api_router.get("/territories", response_model=List[Territory])
async def get_territories(current_user: Dict = Depends(get_current_user)):
    territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
    for territory in territories:
        if isinstance(territory.get('updatedAt'), str):
            territory['updatedAt'] = datetime.fromisoformat(territory['updatedAt'])
        if 'coordinates' in territory and 'center' not in territory:
            coords = territory.get('coordinates', {}).get('coordinates', [[]])[0]
            if coords and len(coords) > 0:
                lats = [c[1] for c in coords]
                lngs = [c[0] for c in coords]
                territory['center'] = {'lat': sum(lats) / len(lats), 'lng': sum(lngs) / len(lngs)}
                territory['radius'] = 5000
    return territories

@api_router.get("/territories/{territory_id}", response_model=Territory)
async def get_territory(territory_id: str, current_user: Dict = Depends(get_current_user)):
    territory = await db.territories.find_one({"id": territory_id}, {"_id": 0})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    if isinstance(territory.get('updatedAt'), str):
        territory['updatedAt'] = datetime.fromisoformat(territory['updatedAt'])
    return Territory(**territory)

@api_router.put("/territories/{territory_id}", response_model=Territory)
async def update_territory(territory_id: str, territory_data: TerritoryUpdate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.COMMUNITY_HEAD])
    
    existing = await db.territories.find_one({"id": territory_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    update_data = territory_data.model_dump(exclude_none=True)
    if 'metrics' in update_data:
        metrics = TerritoryMetrics(**update_data['metrics'])
        ai_insights = predict_appreciation(metrics)
        update_data['aiInsights'] = ai_insights.model_dump()
    
    update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    await db.territories.update_one({"id": territory_id}, {"$set": update_data})
    
    if 'metrics' in update_data:
        history = MetricsHistory(territoryId=territory_id, metrics=metrics, aiInsights=ai_insights)
        history_doc = history.model_dump()
        history_doc['timestamp'] = history_doc['timestamp'].isoformat()
        await db.metrics_history.insert_one(history_doc)
    
    updated = await db.territories.find_one({"id": territory_id}, {"_id": 0})
    broadcast_data = {k: v for k, v in updated.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "territory_updated", "data": broadcast_data}))
    
    if isinstance(updated.get('updatedAt'), str):
        updated['updatedAt'] = datetime.fromisoformat(updated['updatedAt'])
    return Territory(**updated)

@api_router.delete("/territories/{territory_id}")
async def delete_territory(territory_id: str, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN])
    result = await db.territories.delete_one({"id": territory_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Territory not found")
    await manager.broadcast(json.dumps({"type": "territory_deleted", "territoryId": territory_id}))
    return {"message": "Territory deleted successfully"}

# ==================== PIN ROUTES (Channel Partners Access) ====================

@api_router.post("/pins", response_model=Pin)
async def create_pin(pin_data: PinCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.CHANNEL_PARTNER])
    
    user = await db.users.find_one({"id": current_user['user_id']})
    
    ai_insights = None
    if pin_data.generateAIInsights:
        api_key = user.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
        if api_key:
            ai_insights = await generate_pin_ai_insights(pin_data.model_dump(), api_key)
    
    pin = Pin(
        location=pin_data.location, type=pin_data.type, label=pin_data.label,
        description=pin_data.description, address=pin_data.address,
        hasGeofence=pin_data.hasGeofence, geofenceRadius=pin_data.geofenceRadius,
        territoryId=pin_data.territoryId, projectId=pin_data.projectId, eventId=pin_data.eventId,
        aiInsights=ai_insights, createdBy=current_user['user_id'], userName=user['name']
    )
    
    doc = pin.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    await db.pins.insert_one(doc)
    await manager.broadcast(json.dumps({"type": "pin_created", "data": {"id": pin.id, "label": pin.label}}))
    return pin

@api_router.get("/pins", response_model=List[Pin])
async def get_pins(current_user: Dict = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    pins = await db.pins.find(query, {"_id": 0}).to_list(1000)
    for pin in pins:
        if isinstance(pin.get('createdAt'), str):
            pin['createdAt'] = datetime.fromisoformat(pin['createdAt'])
    return pins

@api_router.get("/pins/{pin_id}", response_model=Pin)
async def get_pin(pin_id: str, current_user: Dict = Depends(get_current_user)):
    pin = await db.pins.find_one({"id": pin_id}, {"_id": 0})
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")
    if isinstance(pin.get('createdAt'), str):
        pin['createdAt'] = datetime.fromisoformat(pin['createdAt'])
    return Pin(**pin)

@api_router.put("/pins/{pin_id}", response_model=Pin)
async def update_pin(pin_id: str, pin_data: PinUpdate, current_user: Dict = Depends(get_current_user)):
    existing = await db.pins.find_one({"id": pin_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Pin not found")
    if existing['createdBy'] != current_user['user_id'] and current_user['role'] not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    update_data = pin_data.model_dump(exclude_none=True)
    await db.pins.update_one({"id": pin_id}, {"$set": update_data})
    updated = await db.pins.find_one({"id": pin_id}, {"_id": 0})
    if isinstance(updated.get('createdAt'), str):
        updated['createdAt'] = datetime.fromisoformat(updated['createdAt'])
    await manager.broadcast(json.dumps({"type": "pin_updated", "data": {"id": pin_id}}))
    return Pin(**updated)

@api_router.delete("/pins/{pin_id}")
async def delete_pin(pin_id: str, current_user: Dict = Depends(get_current_user)):
    existing = await db.pins.find_one({"id": pin_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Pin not found")
    if existing['createdBy'] != current_user['user_id'] and current_user['role'] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    await db.pins.delete_one({"id": pin_id})
    await manager.broadcast(json.dumps({"type": "pin_deleted", "pinId": pin_id}))
    return {"message": "Pin deleted successfully"}

# ==================== PROJECT ROUTES ====================

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER])
    
    ai_recommendations = []
    if project_data.generateAIRecommendations:
        user = await db.users.find_one({"id": current_user['user_id']})
        api_key = user.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
        if api_key:
            try:
                client = AsyncOpenAI(api_key=api_key)
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Generate 5 strategic recommendations for this project in Ahmedabad: {project_data.name}. {project_data.description}"}],
                    max_tokens=200
                )
                content = response.choices[0].message.content
                ai_recommendations = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
            except:
                ai_recommendations = ["Focus on local market research", "Engage community stakeholders", "Plan for seasonal variations"]
    
    project = Project(
        name=project_data.name, description=project_data.description, location=project_data.location,
        territoryId=project_data.territoryId, status=project_data.status, budget=project_data.budget,
        startDate=project_data.startDate, endDate=project_data.endDate,
        aiRecommendations=ai_recommendations, createdBy=current_user['user_id']
    )
    
    doc = project.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    if doc.get('startDate'):
        doc['startDate'] = doc['startDate'].isoformat()
    if doc.get('endDate'):
        doc['endDate'] = doc['endDate'].isoformat()
    await db.projects.insert_one(doc)
    await manager.broadcast(json.dumps({"type": "project_created", "data": {"id": project.id, "name": project.name}}))
    return project

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: Dict = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    for project in projects:
        if isinstance(project.get('createdAt'), str):
            project['createdAt'] = datetime.fromisoformat(project['createdAt'])
        if project.get('startDate') and isinstance(project['startDate'], str):
            project['startDate'] = datetime.fromisoformat(project['startDate'])
        if project.get('endDate') and isinstance(project['endDate'], str):
            project['endDate'] = datetime.fromisoformat(project['endDate'])
    return projects

# ==================== EVENT ROUTES ====================

@api_router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER])
    
    user = await db.users.find_one({"id": current_user['user_id']})
    
    ai_predictions = None
    if event_data.generateAIPredictions:
        api_key = user.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
        if api_key:
            try:
                client = AsyncOpenAI(api_key=api_key)
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Predict success factors for this event in Ahmedabad: {event_data.title}. Category: {event_data.category}. Provide JSON with turnout_estimate, success_probability, key_challenges"}],
                    max_tokens=150
                )
                ai_predictions = json.loads(response.choices[0].message.content)
            except:
                ai_predictions = {"turnout_estimate": "Medium", "success_probability": 0.75, "key_challenges": ["Weather", "Accessibility"]}
    
    event = Event(
        title=event_data.title, description=event_data.description, location=event_data.location,
        territoryId=event_data.territoryId, projectId=event_data.projectId,
        eventDate=event_data.eventDate, category=event_data.category,
        attendeesEstimate=event_data.attendeesEstimate, aiPredictions=ai_predictions,
        createdBy=current_user['user_id'], userName=user['name']
    )
    
    doc = event.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    doc['eventDate'] = doc['eventDate'].isoformat()
    await db.events.insert_one(doc)
    await manager.broadcast(json.dumps({"type": "event_created", "data": {"id": event.id, "title": event.title}}))
    return event

@api_router.get("/events", response_model=List[Event])
async def get_events(current_user: Dict = Depends(get_current_user), territory_id: Optional[str] = Query(None), project_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    if project_id:
        query['projectId'] = project_id
    events = await db.events.find(query, {"_id": 0}).sort("eventDate", -1).to_list(1000)
    for event in events:
        if isinstance(event.get('createdAt'), str):
            event['createdAt'] = datetime.fromisoformat(event['createdAt'])
        if isinstance(event.get('eventDate'), str):
            event['eventDate'] = datetime.fromisoformat(event['eventDate'])
    return events

# ==================== SHARE LINK ROUTES ====================

@api_router.post("/share-links")
async def create_share_link(territory_id: str, current_user: Dict = Depends(get_current_user)):
    share_link = ShareLink(territoryId=territory_id, createdBy=current_user['user_id'])
    doc = share_link.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    doc['expiresAt'] = doc['expiresAt'].isoformat()
    await db.share_links.insert_one(doc)
    return {"shareToken": share_link.token, "shareUrl": f"/share/{share_link.token}", "expiresAt": share_link.expiresAt}

@api_router.get("/share-links/validate/{token}")
async def validate_share_link(token: str):
    link = await db.share_links.find_one({"token": token})
    if not link:
        raise HTTPException(status_code=404, detail="Invalid share link")
    expires_at = datetime.fromisoformat(link['expiresAt'])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link expired")
    territory = await db.territories.find_one({"id": link['territoryId']}, {"_id": 0})
    if isinstance(territory.get('updatedAt'), str):
        territory['updatedAt'] = datetime.fromisoformat(territory['updatedAt'])
    return {"territory": Territory(**territory), "token": token}

# ==================== COMMENT ROUTES (Partner Access) ====================

@api_router.post("/comments", response_model=Comment)
async def create_comment(comment_data: CommentCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.PARTNER, UserRole.COMMUNITY_HEAD])
    
    if comment_data.useAI:
        api_key = comment_data.apiKey
        if not api_key:
            user = await db.users.find_one({"id": current_user['user_id']})
            api_key = user.get('openai_api_key')
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key required for AI validation")
        validation = await validate_comment_ai(comment_data.text, api_key)
    else:
        validation = validate_comment_regex(comment_data.text)
    
    if validation['label'] == 'flagged':
        raise HTTPException(status_code=400, detail=f"Comment flagged: {validation['reason']}")
    
    user = await db.users.find_one({"id": current_user['user_id']})
    comment = Comment(
        territoryId=comment_data.territoryId, userId=current_user['user_id'],
        userName=user['name'], text=comment_data.text,
        validationStatus=validation['label'], validationReason=validation['reason'],
        sentiment=validation.get('sentiment', 'neutral')
    )
    doc = comment.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    await db.comments.insert_one(doc)
    return comment

@api_router.get("/comments/{territory_id}", response_model=List[Comment])
async def get_comments(territory_id: str, current_user: Dict = Depends(get_current_user)):
    comments = await db.comments.find({"territoryId": territory_id}, {"_id": 0}).sort("createdAt", -1).to_list(100)
    for comment in comments:
        if isinstance(comment.get('createdAt'), str):
            comment['createdAt'] = datetime.fromisoformat(comment['createdAt'])
    return comments

# ==================== DATA GATHERING ROUTES (Channel Partners Access) ====================

@api_router.post("/data-gathering", response_model=DataGathering)
async def submit_data(form_data: DataGatheringForm, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.CHANNEL_PARTNER])
    
    data_entry = DataGathering(
        territoryId=form_data.territoryId, data=form_data.data,
        submittedBy=current_user['user_id'], shareToken=form_data.shareToken
    )
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.data_gathering.insert_one(doc)
    
    # Update live analytics
    analytics = await update_territory_analytics(form_data.territoryId)
    
    await manager.broadcast(json.dumps({"type": "data_submitted", "territoryId": form_data.territoryId, "analytics": analytics}))
    
    return data_entry

@api_router.post("/data-gathering/public")
async def submit_data_public(form_data: dict):
    share_token = form_data.get('shareToken')
    if not share_token:
        raise HTTPException(status_code=400, detail="Share token required")
    link = await db.share_links.find_one({"token": share_token})
    if not link:
        raise HTTPException(status_code=404, detail="Invalid share link")
    expires_at = datetime.fromisoformat(link['expiresAt'])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link expired")
    data_entry = DataGathering(
        territoryId=link['territoryId'], data=form_data.get('data', {}),
        submittedBy="anonymous", shareToken=share_token
    )
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.data_gathering.insert_one(doc)
    
    # Update live analytics
    analytics = await update_territory_analytics(link['territoryId'])
    
    await manager.broadcast(json.dumps({"type": "data_submitted", "territoryId": link['territoryId'], "analytics": analytics}))
    
    return {"message": "Data submitted successfully", "id": data_entry.id}

@api_router.get("/data-gathering/{territory_id}", response_model=List[DataGathering])
async def get_data_gathering(territory_id: str, current_user: Dict = Depends(get_current_user)):
    data = await db.data_gathering.find({"territoryId": territory_id}, {"_id": 0}).to_list(1000)
    for entry in data:
        if isinstance(entry.get('timestamp'), str):
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
    return data

# ==================== ANALYTICS ROUTES ====================

@api_router.get("/analytics/{territory_id}")
async def get_territory_analytics(territory_id: str, current_user: Dict = Depends(get_current_user)):
    """Get live analytics for a territory"""
    analytics = await analyze_gathered_data(territory_id)
    return analytics

@api_router.post("/analytics/refresh/{territory_id}")
async def refresh_analytics(territory_id: str, current_user: Dict = Depends(get_current_user)):
    """Manually refresh analytics for a territory"""
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER])
    analytics = await update_territory_analytics(territory_id)
    return {"message": "Analytics refreshed successfully", "analytics": analytics}

# ==================== METRICS HISTORY ROUTES ====================

@api_router.get("/metrics-history/{territory_id}", response_model=List[MetricsHistory])
async def get_metrics_history(territory_id: str, current_user: Dict = Depends(get_current_user)):
    history = await db.metrics_history.find({"territoryId": territory_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    for entry in history:
        if isinstance(entry.get('timestamp'), str):
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
    return history

# ==================== AI ANALYSIS ENDPOINT ====================

@api_router.post("/ai/analyze")
async def ai_analyze(request: AIAnalysisRequest, current_user: Dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user['user_id']})
    api_key = user.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key required")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        if request.entityType == "territory":
            territory = await db.territories.find_one({"id": request.entityId})
            prompt = f"Analyze this territory in Ahmedabad: {territory['name']}. Metrics: {territory['metrics']}. Provide strategic insights."
        elif request.entityType == "pin":
            pin = await db.pins.find_one({"id": request.entityId})
            prompt = f"Analyze this location pin in Ahmedabad: {pin['label']} ({pin['type']}). Provide business insights."
        else:
            raise HTTPException(status_code=400, detail="Invalid entity type")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        return {"analysis": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "R Territory AI Engine - Ahmedabad Edition", "version": "4.0", "city": "Ahmedabad", "features": "Live Analytics + RBAC"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "city": "Ahmedabad"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()