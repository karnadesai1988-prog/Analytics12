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

app = FastAPI(title="R Territory - Ahmedabad")
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

class UserRole:
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"
    COMMUNITY_HEAD = "community_head"
    MONITOR = "monitor"
    PARTNER = "partner"
    CHANNEL_PARTNER = "channel_partner"

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
    pincode: Optional[str] = None
    center: Dict[str, float]
    radius: float = 5000
    boundary: Optional[List[List[float]]] = None
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
    pincode: Optional[str] = None
    center: Dict[str, float]
    radius: float = 5000
    boundary: Optional[List[List[float]]] = None
    metrics: TerritoryMetrics = Field(default_factory=TerritoryMetrics)
    restrictions: TerritoryRestrictions = Field(default_factory=TerritoryRestrictions)

class TerritoryUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zone: Optional[str] = None
    center: Optional[Dict[str, float]] = None
    radius: Optional[float] = None
    boundary: Optional[List[List[float]]] = None
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
    hasGeofence: Optional[bool] = None
    geofenceRadius: Optional[float] = None
    territoryId: Optional[str] = None

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

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    return jwt.encode({'user_id': user_id, 'email': email, 'role': role, 'exp': datetime.now(timezone.utc) + timedelta(days=7)}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    return verify_token(credentials.credentials)

def check_permission(user_role: str, required_roles: List[str]):
    if user_role not in required_roles:
        raise HTTPException(status_code=403, detail=f"Access denied. Required: {', '.join(required_roles)}")

async def analyze_gathered_data(territory_id: str) -> Dict[str, Any]:
    try:
        data = await db.data_gathering.find({"territoryId": territory_id}, {"_id": 0}).to_list(1000)
        if not data:
            return {"totalSubmissions": 0, "avgPropertyValue": 0, "avgRentPrice": 0, "avgOccupancyRate": 0, "avgMaintenanceCost": 0, "tenantDistribution": {}, "submissionTrend": "No data", "dataQuality": "N/A"}
        
        pv, rp, occ, mc = [], [], [], []
        tenants = defaultdict(int)
        
        for entry in data:
            d = entry.get('data', {})
            if d.get('propertyValue'): pv.append(float(d['propertyValue']))
            if d.get('rentPrice'): rp.append(float(d['rentPrice']))
            if d.get('occupancyRate'): occ.append(float(d['occupancyRate']))
            if d.get('maintenanceCost'): mc.append(float(d['maintenanceCost']))
            if d.get('tenantType'): tenants[d['tenantType']] += 1
        
        return {
            "totalSubmissions": len(data),
            "avgPropertyValue": round(sum(pv) / len(pv), 2) if pv else 0,
            "avgRentPrice": round(sum(rp) / len(rp), 2) if rp else 0,
            "avgOccupancyRate": round(sum(occ) / len(occ), 2) if occ else 0,
            "avgMaintenanceCost": round(sum(mc) / len(mc), 2) if mc else 0,
            "tenantDistribution": dict(tenants),
            "submissionTrend": "Increasing" if len(data) > 10 else "Growing",
            "dataQuality": "High" if len(data) > 20 else "Medium" if len(data) > 5 else "Low",
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logging.error(f"Error analyzing: {e}")
        return {"error": str(e)}

async def update_territory_analytics(territory_id: str):
    try:
        analytics = await analyze_gathered_data(territory_id)
        await db.territories.update_one({"id": territory_id}, {"$set": {"liveAnalytics": analytics}})
        await manager.broadcast(json.dumps({"type": "analytics_updated", "territoryId": territory_id, "analytics": analytics}))
        return analytics
    except Exception as e:
        logging.error(f"Error updating analytics: {e}")
        return None

def predict_appreciation(metrics: TerritoryMetrics) -> AIInsights:
    try:
        inv_factor = min(np.log10(metrics.investments + 1) / 2, 1.0)
        appreciation = (inv_factor * 5 + (metrics.livabilityIndex / 10) * 5 + (metrics.govtInfra / 10) * 4 + (metrics.qualityOfProject / 10) * 4 + (metrics.roads / 10) * 3 + (1 - metrics.crimeRate / 10) * 2 + (1 - metrics.airPollutionIndex / 10) * 2)
        demand = min(((metrics.populationDensity / 1000) * 30 + (metrics.buildings / 200) * 30 + inv_factor * 40), 100)
        confidence = min(0.70 + (metrics.qualityOfProject / 50) + (metrics.govtInfra / 50), 0.95)
        suggestions = []
        if metrics.livabilityIndex < 6: suggestions.append("Improve livability")
        if metrics.roads < 7: suggestions.append("Enhance roads")
        if metrics.crimeRate > 5: suggestions.append("Improve safety")
        return AIInsights(appreciationPercent=round(max(0, min(appreciation, 25)), 2), demandPressure=round(max(0, demand), 2), confidenceScore=round(confidence, 2), aiSuggestions=suggestions)
    except:
        return AIInsights(appreciationPercent=0, demandPressure=0, confidenceScore=0.5, aiSuggestions=[])

def validate_comment_regex(text: str) -> Dict:
    banned = [r'spam', r'fake', r'abuse']
    for p in banned:
        if re.search(p, text, re.IGNORECASE):
            return {"label": "flagged", "reason": f"Pattern: {p}", "sentiment": "negative"}
    return {"label": "valid", "reason": "Clean", "sentiment": "neutral"}

async def validate_comment_ai(text: str, api_key: str) -> Dict:
    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": "Analyze comment. JSON: {status: 'VALID'/'FLAGGED', reason: string, sentiment: 'positive'/'neutral'/'negative'}"}, {"role": "user", "content": text}], max_tokens=100)
        result = json.loads(response.choices[0].message.content)
        return {"label": "flagged" if result.get("status") == "FLAGGED" else "valid", "reason": result.get("reason", "Done"), "sentiment": result.get("sentiment", "neutral")}
    except:
        return {"label": "valid", "reason": "AI unavailable", "sentiment": "neutral"}

# ==================== AUTH ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserRegister):
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email exists")
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
    return {"token": create_token(user['id'], user['email'], user['role']), "user": {"id": user['id'], "email": user['email'], "name": user['name'], "role": user['role']}}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: Dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/auth/config-api-key")
async def configure_api_key(config: APIKeyConfig, current_user: Dict = Depends(get_current_user)):
    await db.users.update_one({"id": current_user['user_id']}, {"$set": {"openai_api_key": config.openai_api_key}})
    return {"message": "API key configured"}

# ==================== TERRITORIES ====================

@api_router.post("/territories", response_model=Territory)
async def create_territory(territory_data: TerritoryCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.COMMUNITY_HEAD])
    ai_insights = predict_appreciation(territory_data.metrics)
    territory = Territory(**{**territory_data.model_dump(), 'aiInsights': ai_insights, 'liveAnalytics': None, 'createdBy': current_user['user_id']})
    doc = territory.model_dump()
    doc['updatedAt'] = doc['updatedAt'].isoformat()
    await db.territories.insert_one(doc)
    await manager.broadcast(json.dumps({"type": "territory_created", "data": {"id": territory.id, "name": territory.name}}))
    return territory

@api_router.get("/territories", response_model=List[Territory])
async def get_territories(current_user: Dict = Depends(get_current_user)):
    territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
    for t in territories:
        if isinstance(t.get('updatedAt'), str): t['updatedAt'] = datetime.fromisoformat(t['updatedAt'])
        if 'coordinates' in t and 'center' not in t:
            coords = t.get('coordinates', {}).get('coordinates', [[]])[0]
            if coords:
                lats, lngs = [c[1] for c in coords], [c[0] for c in coords]
                t['center'] = {'lat': sum(lats)/len(lats), 'lng': sum(lngs)/len(lngs)}
                t['radius'] = 5000
    return territories

@api_router.put("/territories/{territory_id}", response_model=Territory)
async def update_territory(territory_id: str, territory_data: TerritoryUpdate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.COMMUNITY_HEAD])
    if not await db.territories.find_one({"id": territory_id}):
        raise HTTPException(status_code=404, detail="Not found")
    update_data = territory_data.model_dump(exclude_none=True)
    if 'metrics' in update_data:
        update_data['aiInsights'] = predict_appreciation(TerritoryMetrics(**update_data['metrics'])).model_dump()
    update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    await db.territories.update_one({"id": territory_id}, {"$set": update_data})
    updated = await db.territories.find_one({"id": territory_id}, {"_id": 0})
    await manager.broadcast(json.dumps({"type": "territory_updated", "territoryId": territory_id}))
    if isinstance(updated.get('updatedAt'), str): updated['updatedAt'] = datetime.fromisoformat(updated['updatedAt'])
    return Territory(**updated)

@api_router.delete("/territories/{territory_id}")
async def delete_territory(territory_id: str, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN])
    if (await db.territories.delete_one({"id": territory_id})).deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    await manager.broadcast(json.dumps({"type": "territory_deleted", "territoryId": territory_id}))
    return {"message": "Deleted"}

# ==================== PINS ====================

@api_router.post("/pins", response_model=Pin)
async def create_pin(pin_data: PinCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.CHANNEL_PARTNER])
    user = await db.users.find_one({"id": current_user['user_id']})
    pin = Pin(**{**pin_data.model_dump(exclude={'generateAIInsights'}), 'aiInsights': None, 'createdBy': current_user['user_id'], 'userName': user['name']})
    doc = pin.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    await db.pins.insert_one(doc)
    await manager.broadcast(json.dumps({"type": "pin_created", "pinId": pin.id}))
    return pin

@api_router.get("/pins", response_model=List[Pin])
async def get_pins(current_user: Dict = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id: query['territoryId'] = territory_id
    pins = await db.pins.find(query, {"_id": 0}).to_list(1000)
    for p in pins:
        if isinstance(p.get('createdAt'), str): p['createdAt'] = datetime.fromisoformat(p['createdAt'])
    return pins

@api_router.put("/pins/{pin_id}", response_model=Pin)
async def update_pin(pin_id: str, pin_data: PinUpdate, current_user: Dict = Depends(get_current_user)):
    existing = await db.pins.find_one({"id": pin_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")
    if existing['createdBy'] != current_user['user_id'] and current_user['role'] not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="No permission")
    await db.pins.update_one({"id": pin_id}, {"$set": pin_data.model_dump(exclude_none=True)})
    updated = await db.pins.find_one({"id": pin_id}, {"_id": 0})
    if isinstance(updated.get('createdAt'), str): updated['createdAt'] = datetime.fromisoformat(updated['createdAt'])
    await manager.broadcast(json.dumps({"type": "pin_updated", "pinId": pin_id}))
    return Pin(**updated)

@api_router.delete("/pins/{pin_id}")
async def delete_pin(pin_id: str, current_user: Dict = Depends(get_current_user)):
    existing = await db.pins.find_one({"id": pin_id})
    if not existing or (existing['createdBy'] != current_user['user_id'] and current_user['role'] != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="No permission")
    await db.pins.delete_one({"id": pin_id})
    await manager.broadcast(json.dumps({"type": "pin_deleted", "pinId": pin_id}))
    return {"message": "Deleted"}

# ==================== COMMENTS ====================

@api_router.post("/comments", response_model=Comment)
async def create_comment(comment_data: CommentCreate, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.PARTNER, UserRole.COMMUNITY_HEAD])
    validation = validate_comment_regex(comment_data.text)
    if comment_data.useAI:
        user = await db.users.find_one({"id": current_user['user_id']})
        api_key = comment_data.apiKey or user.get('openai_api_key')
        if api_key: validation = await validate_comment_ai(comment_data.text, api_key)
    if validation['label'] == 'flagged':
        raise HTTPException(status_code=400, detail=f"Flagged: {validation['reason']}")
    user = await db.users.find_one({"id": current_user['user_id']})
    comment = Comment(territoryId=comment_data.territoryId, userId=current_user['user_id'], userName=user['name'], text=comment_data.text, validationStatus=validation['label'], validationReason=validation['reason'], sentiment=validation.get('sentiment'))
    doc = comment.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    await db.comments.insert_one(doc)
    return comment

@api_router.get("/comments/{territory_id}", response_model=List[Comment])
async def get_comments(territory_id: str, current_user: Dict = Depends(get_current_user)):
    comments = await db.comments.find({"territoryId": territory_id}, {"_id": 0}).sort("createdAt", -1).to_list(100)
    for c in comments:
        if isinstance(c.get('createdAt'), str): c['createdAt'] = datetime.fromisoformat(c['createdAt'])
    return comments

# ==================== DATA GATHERING ====================

@api_router.post("/data-gathering", response_model=DataGathering)
async def submit_data(form_data: DataGatheringForm, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER, UserRole.CHANNEL_PARTNER])
    data_entry = DataGathering(territoryId=form_data.territoryId, data=form_data.data, submittedBy=current_user['user_id'], shareToken=form_data.shareToken)
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.data_gathering.insert_one(doc)
    analytics = await update_territory_analytics(form_data.territoryId)
    await manager.broadcast(json.dumps({"type": "data_submitted", "territoryId": form_data.territoryId, "analytics": analytics}))
    return data_entry

@api_router.post("/data-gathering/public")
async def submit_data_public(form_data: dict):
    token = form_data.get('shareToken')
    if not token:
        raise HTTPException(status_code=400, detail="Token required")
    link = await db.share_links.find_one({"token": token})
    if not link or datetime.fromisoformat(link['expiresAt']) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invalid/expired")
    data_entry = DataGathering(territoryId=link['territoryId'], data=form_data.get('data', {}), submittedBy="anonymous", shareToken=token)
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.data_gathering.insert_one(doc)
    analytics = await update_territory_analytics(link['territoryId'])
    await manager.broadcast(json.dumps({"type": "data_submitted", "territoryId": link['territoryId'], "analytics": analytics}))
    return {"message": "Submitted", "id": data_entry.id}

@api_router.get("/data-gathering/{territory_id}", response_model=List[DataGathering])
async def get_data_gathering(territory_id: str, current_user: Dict = Depends(get_current_user)):
    data = await db.data_gathering.find({"territoryId": territory_id}, {"_id": 0}).to_list(1000)
    for e in data:
        if isinstance(e.get('timestamp'), str): e['timestamp'] = datetime.fromisoformat(e['timestamp'])
    return data

# ==================== ANALYTICS ====================

@api_router.get("/analytics/{territory_id}")
async def get_territory_analytics(territory_id: str, current_user: Dict = Depends(get_current_user)):
    return await analyze_gathered_data(territory_id)

@api_router.post("/analytics/refresh/{territory_id}")
async def refresh_analytics(territory_id: str, current_user: Dict = Depends(get_current_user)):
    check_permission(current_user['role'], [UserRole.ADMIN, UserRole.MANAGER])
    analytics = await update_territory_analytics(territory_id)
    return {"message": "Refreshed", "analytics": analytics}

@api_router.get("/metrics-history/{territory_id}", response_model=List[MetricsHistory])
async def get_metrics_history(territory_id: str, current_user: Dict = Depends(get_current_user)):
    history = await db.metrics_history.find({"territoryId": territory_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    for e in history:
        if isinstance(e.get('timestamp'), str): e['timestamp'] = datetime.fromisoformat(e['timestamp'])
    return history

# ==================== SHARE LINKS ====================

@api_router.post("/share-links")
async def create_share_link(territory_id: str, current_user: Dict = Depends(get_current_user)):
    link = ShareLink(territoryId=territory_id, createdBy=current_user['user_id'])
    doc = link.model_dump()
    doc['createdAt'], doc['expiresAt'] = doc['createdAt'].isoformat(), doc['expiresAt'].isoformat()
    await db.share_links.insert_one(doc)
    return {"shareToken": link.token, "shareUrl": f"/share/{link.token}", "expiresAt": link.expiresAt}

@api_router.get("/share-links/validate/{token}")
async def validate_share_link(token: str):
    link = await db.share_links.find_one({"token": token})
    if not link or datetime.fromisoformat(link['expiresAt']) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Invalid/expired")
    territory = await db.territories.find_one({"id": link['territoryId']}, {"_id": 0})
    if isinstance(territory.get('updatedAt'), str): territory['updatedAt'] = datetime.fromisoformat(territory['updatedAt'])
    return {"territory": Territory(**territory), "token": token}

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@api_router.get("/")
async def root():
    return {"message": "R Territory - Ahmedabad", "version": "5.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "city": "Ahmedabad"}

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()