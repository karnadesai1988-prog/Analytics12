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
import httpx

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
    pincode_api_url: Optional[str] = None
    pincode_api_key: Optional[str] = None
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
    pincode: str
    center: Dict[str, float]
    radius: float = 2500  # 2.5km radius = 5km diameter
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
    pincode: str
    center: Optional[Dict[str, float]] = None
    radius: float = 2500  # 2.5km radius = 5km diameter
    metrics: TerritoryMetrics = Field(default_factory=TerritoryMetrics)
    restrictions: TerritoryRestrictions = Field(default_factory=TerritoryRestrictions)

class TerritoryUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zone: Optional[str] = None
    pincode: Optional[str] = None
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
    hasGeofence: Optional[bool] = None
    geofenceRadius: Optional[float] = None
    territoryId: Optional[str] = None

class CommentCreate(BaseModel):
    territoryId: str
    text: str
    zone: Optional[str] = None
    photo: Optional[str] = None  # Base64 encoded image
    useAI: bool = False
    apiKey: Optional[str] = None

class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    userId: str
    userName: str
    text: str
    zone: Optional[str] = None
    photo: Optional[str] = None
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
    pincode_api_url: Optional[str] = None
    pincode_api_key: Optional[str] = None

class PincodeBoundaryRequest(BaseModel):
    pincode: str

# Gujarat / Ahmedabad Fixed Pincode Boundaries (Sample Data for Testing)
GUJARAT_PINCODE_BOUNDARIES = {
    "380001": {"boundary": [[23.0340, 72.5840], [23.0380, 72.5900], [23.0370, 72.5960], [23.0320, 72.5930], [23.0340, 72.5840]], "center": {"lat": 23.0350, "lng": 72.5910}},
    "380004": {"boundary": [[23.0190, 72.5690], [23.0250, 72.5750], [23.0230, 72.5810], [23.0180, 72.5790], [23.0190, 72.5690]], "center": {"lat": 23.0215, "lng": 72.5750}},
    "380006": {"boundary": [[23.0270, 72.5590], [23.0330, 72.5650], [23.0310, 72.5710], [23.0260, 72.5690], [23.0270, 72.5590]], "center": {"lat": 23.0293, "lng": 72.5650}},
    "380009": {"boundary": [[23.0390, 72.5490], [23.0450, 72.5550], [23.0430, 72.5610], [23.0380, 72.5590], [23.0390, 72.5490]], "center": {"lat": 23.0413, "lng": 72.5560}},
    "380013": {"boundary": [[23.0520, 72.5380], [23.0580, 72.5440], [23.0560, 72.5500], [23.0510, 72.5480], [23.0520, 72.5380]], "center": {"lat": 23.0543, "lng": 72.5450}},
    "380015": {"boundary": [[23.0090, 72.5790], [23.0150, 72.5850], [23.0130, 72.5910], [23.0080, 72.5890], [23.0090, 72.5790]], "center": {"lat": 23.0113, "lng": 72.5860}},
    "380022": {"boundary": [[23.0680, 72.5260], [23.0740, 72.5320], [23.0720, 72.5380], [23.0670, 72.5360], [23.0680, 72.5260]], "center": {"lat": 23.0703, "lng": 72.5330}},
    "380024": {"boundary": [[23.0180, 72.4880], [23.0240, 72.4940], [23.0220, 72.5000], [23.0170, 72.4980], [23.0180, 72.4880]], "center": {"lat": 23.0203, "lng": 72.4950}},
    "380052": {"boundary": [[23.0490, 72.5390], [23.0550, 72.5450], [23.0530, 72.5510], [23.0480, 72.5490], [23.0490, 72.5390]], "center": {"lat": 23.0513, "lng": 72.5460}},
    "380054": {"boundary": [[23.0140, 72.4890], [23.0200, 72.4950], [23.0180, 72.5010], [23.0130, 72.4990], [23.0140, 72.4890]], "center": {"lat": 23.0163, "lng": 72.4960}},
    "380058": {"boundary": [[22.9980, 72.5880], [23.0040, 72.5940], [23.0020, 72.6000], [22.9970, 72.5980], [22.9980, 72.5880]], "center": {"lat": 23.0003, "lng": 72.5950}},
    "380061": {"boundary": [[23.0590, 72.5290], [23.0650, 72.5350], [23.0630, 72.5410], [23.0580, 72.5390], [23.0590, 72.5290]], "center": {"lat": 23.0613, "lng": 72.5360}},
    "380063": {"boundary": [[23.0270, 72.5100], [23.0330, 72.5160], [23.0310, 72.5220], [23.0260, 72.5200], [23.0270, 72.5100]], "center": {"lat": 23.0293, "lng": 72.5170}},
    "382210": {"boundary": [[23.1020, 72.5950], [23.1080, 72.6010], [23.1060, 72.6070], [23.1010, 72.6050], [23.1020, 72.5950]], "center": {"lat": 23.1043, "lng": 72.6020}},
    "382330": {"boundary": [[23.0820, 72.6140], [23.0880, 72.6200], [23.0860, 72.6260], [23.0810, 72.6240], [23.0820, 72.6140]], "center": {"lat": 23.0843, "lng": 72.6210}},
    "382340": {"boundary": [[23.0380, 72.6280], [23.0440, 72.6340], [23.0420, 72.6400], [23.0370, 72.6380], [23.0380, 72.6280]], "center": {"lat": 23.0403, "lng": 72.6350}},
    "382350": {"boundary": [[23.1180, 72.5420], [23.1240, 72.5480], [23.1220, 72.5540], [23.1170, 72.5520], [23.1180, 72.5420]], "center": {"lat": 23.1203, "lng": 72.5490}},
    "382415": {"boundary": [[23.0120, 72.6480], [23.0180, 72.6540], [23.0160, 72.6600], [23.0110, 72.6580], [23.0120, 72.6480]], "center": {"lat": 23.0143, "lng": 72.6550}},
    "382418": {"boundary": [[22.9820, 72.6180], [22.9880, 72.6240], [22.9860, 72.6300], [22.9810, 72.6280], [22.9820, 72.6180]], "center": {"lat": 22.9843, "lng": 72.6250}},
    "382424": {"boundary": [[22.9520, 72.5980], [22.9580, 72.6040], [22.9560, 72.6100], [22.9510, 72.6080], [22.9520, 72.5980]], "center": {"lat": 22.9543, "lng": 72.6050}},
}

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    user = await db.users.find_one({"id": payload['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

def check_role(allowed_roles: List[str]):
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

def validate_comment_regex(text: str) -> tuple:
    prohibited = ['spam', 'viagra', 'casino', 'lottery']
    for word in prohibited:
        if re.search(rf'\b{word}\b', text, re.IGNORECASE):
            return False, f"Prohibited content detected: {word}"
    if len(text) < 3:
        return False, "Comment too short"
    if len(text) > 2000:
        return False, "Comment too long"
    return True, "Valid"

async def validate_comment_ai(text: str, api_key: str) -> tuple:
    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "You are a content moderation assistant for a real estate territory platform. Analyze if the comment is appropriate, spam-free, and constructive. Respond with JSON: {\"valid\": true/false, \"reason\": \"explanation\", \"sentiment\": \"positive/negative/neutral\"}"
            }, {
                "role": "user",
                "content": f"Comment: {text}"
            }],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result['valid'], result['reason'], result.get('sentiment', 'neutral')
    except Exception as e:
        return True, f"AI validation failed: {str(e)}", "neutral"

def calculate_ai_insights(metrics: TerritoryMetrics) -> AIInsights:
    appreciation = (
        metrics.investments * 0.25 +
        metrics.govtInfra * 0.2 +
        metrics.qualityOfProject * 0.15 +
        metrics.livabilityIndex * 0.15 -
        metrics.airPollutionIndex * 0.1 -
        metrics.crimeRate * 0.1 +
        metrics.roads * 0.05
    ) / 10
    demand = (metrics.populationDensity * 0.4 + metrics.buildings * 0.3 + metrics.investments * 0.3) / 10
    confidence = min(95, max(60, 70 + (metrics.govtInfra - 5) * 3))
    suggestions = []
    if metrics.airPollutionIndex > 7:
        suggestions.append("High pollution - consider green initiatives")
    if metrics.crimeRate > 6:
        suggestions.append("Crime rate elevated - security improvements recommended")
    if metrics.govtInfra < 5:
        suggestions.append("Infrastructure needs development")
    if metrics.livabilityIndex > 7:
        suggestions.append("Strong livability - good for families")
    return AIInsights(appreciationPercent=round(appreciation, 2), demandPressure=round(demand, 2), confidenceScore=round(confidence, 2), aiSuggestions=suggestions)

@api_router.post("/auth/signup")
async def signup(user: UserRegister):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "role": user.role,
        "openai_api_key": None,
        "pincode_api_url": None,
        "pincode_api_key": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_doc['id'], user_doc['email'], user_doc['role'])
    return {"token": token, "user": {"id": user_doc['id'], "email": user_doc['email'], "name": user_doc['name'], "role": user_doc['role']}}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user['id'], user['email'], user['role'])
    return {"token": token, "user": {"id": user['id'], "email": user['email'], "name": user['name'], "role": user['role']}}

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return user

@api_router.post("/auth/config-api-key")
async def config_api_key(config: APIKeyConfig, user: User = Depends(get_current_user)):
    update_data = {}
    if config.openai_api_key:
        update_data["openai_api_key"] = config.openai_api_key
    if config.pincode_api_url:
        update_data["pincode_api_url"] = config.pincode_api_url
    if config.pincode_api_key:
        update_data["pincode_api_key"] = config.pincode_api_key
    await db.users.update_one({"id": user.id}, {"$set": update_data})
    return {"message": "API configuration updated successfully"}

@api_router.post("/pincode/boundary")
async def get_pincode_boundary(request: PincodeBoundaryRequest, user: User = Depends(get_current_user)):
    # First check if we have fixed boundary data for Gujarat pincodes
    if request.pincode in GUJARAT_PINCODE_BOUNDARIES:
        data = GUJARAT_PINCODE_BOUNDARIES[request.pincode]
        return {"boundary": data["boundary"], "center": data["center"], "source": "local_database"}
    
    # If not in local database, try external API
    if not user.pincode_api_url:
        raise HTTPException(
            status_code=400, 
            detail=f"Pincode {request.pincode} not found in local database. Please configure Pincode API in Settings for other pincodes."
        )
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if user.pincode_api_key:
                headers['Authorization'] = f'Bearer {user.pincode_api_key}'
            response = await client.get(
                user.pincode_api_url,
                params={'pincode': request.pincode},
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if 'boundary' in data:
                return {"boundary": data['boundary'], "center": data.get('center'), "source": "external_api"}
            else:
                raise HTTPException(status_code=400, detail="Invalid response from Pincode API")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pincode API error: {str(e)}")

@api_router.post("/territories")
async def create_territory(territory: TerritoryCreate, user: User = Depends(check_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.PARTNER]))):
    # If center is not provided, get it from pincode
    center = territory.center
    if not center:
        # First check if we have fixed boundary data for Gujarat pincodes
        if territory.pincode in GUJARAT_PINCODE_BOUNDARIES:
            center = GUJARAT_PINCODE_BOUNDARIES[territory.pincode]["center"]
        else:
            # If not in local database, try external API
            if not user.pincode_api_url:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Pincode {territory.pincode} not found in local database. Please configure Pincode API in Settings or provide center coordinates."
                )
            
            try:
                async with httpx.AsyncClient() as client:
                    headers = {}
                    if user.pincode_api_key:
                        headers['Authorization'] = f'Bearer {user.pincode_api_key}'
                    response = await client.get(
                        user.pincode_api_url,
                        params={'pincode': territory.pincode},
                        headers=headers,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    if 'center' in data:
                        center = data['center']
                    else:
                        raise HTTPException(status_code=400, detail="Invalid response from Pincode API - no center coordinates")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Pincode API error: {str(e)}")
    
    ai_insights = calculate_ai_insights(territory.metrics)
    territory_doc = {
        "id": str(uuid.uuid4()),
        **territory.model_dump(),
        "center": center,
        "aiInsights": ai_insights.model_dump(),
        "createdBy": user.id,
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
    await db.territories.insert_one(territory_doc)
    # Remove MongoDB ObjectId before broadcasting
    broadcast_data = {k: v for k, v in territory_doc.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "territory_created", "data": broadcast_data}))
    return Territory(**territory_doc)

@api_router.get("/territories", response_model=List[Territory])
async def get_territories(user: User = Depends(get_current_user)):
    territories = await db.territories.find().to_list(length=None)
    # Handle legacy territories that don't have required fields
    result = []
    for t in territories:
        # Skip territories missing required fields (legacy data)
        if 'pincode' not in t or 'center' not in t:
            continue
        result.append(Territory(**t))
    return result

@api_router.get("/territories/{territory_id}", response_model=Territory)
async def get_territory(territory_id: str, user: User = Depends(get_current_user)):
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    # Check if territory has required fields (skip legacy data)
    if 'pincode' not in territory or 'center' not in territory:
        raise HTTPException(status_code=404, detail="Territory data incompatible")
    return Territory(**territory)

@api_router.put("/territories/{territory_id}")
async def update_territory(territory_id: str, territory_update: TerritoryUpdate, user: User = Depends(check_role([UserRole.ADMIN, UserRole.MANAGER]))):
    existing = await db.territories.find_one({"id": territory_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Territory not found")
    update_data = {k: v for k, v in territory_update.model_dump(exclude_unset=True).items() if v is not None}
    update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    if 'metrics' in update_data:
        update_data['aiInsights'] = calculate_ai_insights(TerritoryMetrics(**update_data['metrics'])).model_dump()
    await db.territories.update_one({"id": territory_id}, {"$set": update_data})
    updated = await db.territories.find_one({"id": territory_id})
    # Remove MongoDB ObjectId before broadcasting
    broadcast_data = {k: v for k, v in updated.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "territory_updated", "data": broadcast_data}))
    return Territory(**updated)

@api_router.delete("/territories/{territory_id}")
async def delete_territory(territory_id: str, user: User = Depends(check_role([UserRole.ADMIN]))):
    result = await db.territories.delete_one({"id": territory_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Territory not found")
    await manager.broadcast(json.dumps({"type": "territory_deleted", "id": territory_id}))
    return {"message": "Territory deleted"}

@api_router.post("/pins")
async def create_pin(pin: PinCreate, user: User = Depends(check_role([UserRole.ADMIN, UserRole.PARTNER]))):
    pin_doc = {
        "id": str(uuid.uuid4()),
        **pin.model_dump(),
        "createdBy": user.id,
        "userName": user.name,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    if pin.generateAIInsights and user.openai_api_key:
        try:
            client = AsyncOpenAI(api_key=user.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": "Generate brief insights for this location pin in JSON format: {\"insights\": {\"rating\": 1-10, \"summary\": \"brief text\"}}"
                }, {
                    "role": "user",
                    "content": f"Type: {', '.join(pin.type)}, Label: {pin.label}, Description: {pin.description or 'N/A'}"
                }],
                response_format={"type": "json_object"}
            )
            pin_doc['aiInsights'] = json.loads(response.choices[0].message.content)
        except:
            pin_doc['aiInsights'] = None
    await db.pins.insert_one(pin_doc)
    # Remove MongoDB ObjectId before broadcasting
    broadcast_data = {k: v for k, v in pin_doc.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "pin_created", "data": broadcast_data}))
    return Pin(**pin_doc)

@api_router.get("/pins", response_model=List[Pin])
async def get_pins(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    pins = await db.pins.find(query).to_list(length=None)
    return [Pin(**p) for p in pins]

@api_router.get("/pins/{pin_id}", response_model=Pin)
async def get_pin(pin_id: str, user: User = Depends(get_current_user)):
    pin = await db.pins.find_one({"id": pin_id})
    if not pin:
        raise HTTPException(status_code=404, detail="Pin not found")
    return Pin(**pin)

@api_router.put("/pins/{pin_id}")
async def update_pin(pin_id: str, pin_update: PinUpdate, user: User = Depends(check_role([UserRole.ADMIN, UserRole.PARTNER]))):
    existing = await db.pins.find_one({"id": pin_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Pin not found")
    if existing['createdBy'] != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can only edit your own pins")
    update_data = {k: v for k, v in pin_update.model_dump(exclude_unset=True).items() if v is not None}
    await db.pins.update_one({"id": pin_id}, {"$set": update_data})
    updated = await db.pins.find_one({"id": pin_id})
    # Remove MongoDB ObjectId before broadcasting
    broadcast_data = {k: v for k, v in updated.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "pin_updated", "data": broadcast_data}))
    return Pin(**updated)

@api_router.delete("/pins/{pin_id}")
async def delete_pin(pin_id: str, user: User = Depends(check_role([UserRole.ADMIN, UserRole.PARTNER]))):
    existing = await db.pins.find_one({"id": pin_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Pin not found")
    if existing['createdBy'] != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can only delete your own pins")
    result = await db.pins.delete_one({"id": pin_id})
    await manager.broadcast(json.dumps({"type": "pin_deleted", "id": pin_id}))
    return {"message": "Pin deleted"}

@api_router.post("/comments")
async def create_comment(comment: CommentCreate, user: User = Depends(get_current_user)):
    is_valid, reason = validate_comment_regex(comment.text)
    sentiment = "neutral"
    if comment.useAI:
        api_key = comment.apiKey or user.openai_api_key
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key required for AI validation")
        is_valid, reason, sentiment = await validate_comment_ai(comment.text, api_key)
    comment_doc = {
        "id": str(uuid.uuid4()),
        "territoryId": comment.territoryId,
        "userId": user.id,
        "userName": user.name,
        "text": comment.text,
        "zone": comment.zone,
        "photo": comment.photo,
        "validationStatus": "approved" if is_valid else "rejected",
        "validationReason": reason,
        "sentiment": sentiment,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await db.comments.insert_one(comment_doc)
    # Remove MongoDB ObjectId before broadcasting
    broadcast_data = {k: v for k, v in comment_doc.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "comment_created", "data": broadcast_data}))
    return Comment(**comment_doc)

@api_router.get("/comments", response_model=List[Comment])
async def get_comments(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    comments = await db.comments.find(query).sort("createdAt", -1).to_list(length=None)
    return [Comment(**c) for c in comments]

@api_router.post("/data-gathering")
async def submit_data(data: DataGatheringForm, user: User = Depends(check_role([UserRole.ADMIN, UserRole.PARTNER, UserRole.MANAGER]))):
    data_doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.data_gathering.insert_one(data_doc)
    territory = await db.territories.find_one({"id": data.territoryId})
    if territory:
        new_metrics = territory.get('metrics', {})
        for key, value in data.data.items():
            if key in new_metrics and isinstance(value, (int, float)):
                new_metrics[key] = value
        ai_insights = calculate_ai_insights(TerritoryMetrics(**new_metrics))
        await db.territories.update_one(
            {"id": data.territoryId},
            {"$set": {"metrics": new_metrics, "aiInsights": ai_insights.model_dump(), "updatedAt": datetime.now(timezone.utc).isoformat()}}
        )
        await db.metrics_history.insert_one({
            "id": str(uuid.uuid4()),
            "territoryId": data.territoryId,
            "metrics": new_metrics,
            "aiInsights": ai_insights.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        await manager.broadcast(json.dumps({"type": "metrics_updated", "territoryId": data.territoryId, "metrics": new_metrics, "aiInsights": ai_insights.model_dump()}))
    return DataGathering(**data_doc)

@api_router.get("/data-gathering", response_model=List[DataGathering])
async def get_data_gathering(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    data = await db.data_gathering.find(query).sort("timestamp", -1).to_list(length=None)
    return [DataGathering(**d) for d in data]

@api_router.post("/share-links")
async def create_share_link(territory_id: str, user: User = Depends(check_role([UserRole.ADMIN, UserRole.MANAGER]))):
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    share_link_doc = {
        "id": str(uuid.uuid4()),
        "token": secrets.token_urlsafe(32),
        "territoryId": territory_id,
        "createdBy": user.id,
        "expiresAt": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await db.share_links.insert_one(share_link_doc)
    return ShareLink(**share_link_doc)

@api_router.get("/share-links/{token}")
async def get_share_link(token: str):
    link = await db.share_links.find_one({"token": token})
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    if datetime.fromisoformat(link['expiresAt']) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link expired")
    return ShareLink(**link)

@api_router.get("/analytics/metrics-history", response_model=List[MetricsHistory])
async def get_metrics_history(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query['territoryId'] = territory_id
    history = await db.metrics_history.find(query).sort("timestamp", -1).to_list(length=100)
    return [MetricsHistory(**h) for h in history]

@api_router.get("/analytics/dashboard")
async def get_dashboard_analytics(user: User = Depends(get_current_user)):
    territories = await db.territories.find().to_list(length=None)
    total_investments = sum(t.get('metrics', {}).get('investments', 0) for t in territories)
    avg_appreciation = sum(t.get('aiInsights', {}).get('appreciationPercent', 0) for t in territories) / len(territories) if territories else 0
    total_buildings = sum(t.get('metrics', {}).get('buildings', 0) for t in territories)
    avg_livability = sum(t.get('metrics', {}).get('livabilityIndex', 0) for t in territories) / len(territories) if territories else 0
    return {
        "totalTerritories": len(territories),
        "totalInvestments": round(total_investments, 2),
        "avgAppreciation": round(avg_appreciation, 2),
        "totalBuildings": total_buildings,
        "avgLivability": round(avg_livability, 2)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "R Territory AI - Backend Running", "status": "operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
