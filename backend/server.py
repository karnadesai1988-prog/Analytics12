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

class TerritoryRating(BaseModel):
    totalScore: float = 0
    pinTypeScores: Dict[str, float] = {}
    pinTypeCounts: Dict[str, int] = {}
    topContributors: List[Dict[str, Any]] = []

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
    rating: Optional[TerritoryRating] = None
    liveAnalytics: Optional[Dict[str, Any]] = None
    createdBy: str
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TerritoryCreate(BaseModel):
    name: str
    city: str
    zone: Optional[str] = None
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

class CommunityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    territoryId: str
    photo: Optional[str] = None
    canJoin: bool = True

class Community(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    territoryId: str
    photo: Optional[str] = None
    canJoin: bool = True
    createdBy: str
    members: List[str] = []  # User IDs
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PostCreate(BaseModel):
    communityId: str
    text: str
    location: Dict[str, float]
    photo: Optional[str] = None

class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    communityId: str
    userId: str
    userName: str
    text: str
    location: Dict[str, float]
    photo: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Professional(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    professionType: str  # Channel Partner, Developer, Broker, Architect, Lawyer, Vendor
    territoryId: str
    verified: bool = False
    photo: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    userId: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    name: str
    status: str = "Under Construction"
    developerName: str
    priceRange: str
    configuration: str
    location: Dict[str, float]
    territoryId: str
    brochureUrl: Optional[str] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: str  # Under Construction, Ready, Possession Soon
    developerName: str
    priceRange: str
    configuration: str
    location: Dict[str, float]
    territoryId: str
    brochureUrl: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Opportunity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    type: str  # Buyer, Rental, Land, JointDevelopment
    territoryId: str
    description: str
    claimedBy: Optional[str] = None
    createdBy: str
    isNew: bool = True
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventCreate(BaseModel):
    title: str
    date: str  # ISO format date string
    location: str
    territoryId: str
    organizer: str

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    date: datetime
    location: str
    territoryId: str
    organizer: str
    status: str  # upcoming, past
    rsvpList: List[str] = []
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

# Pin type weightages for territory rating
PIN_TYPE_WEIGHTAGES = {
    'job': 9,
    'supplier': 8,
    'vendor': 8,
    'shop': 7,
    'office': 9,
    'warehouse': 7,
    'service_center': 6,
    'event_venue': 6,
    'project_site': 10,
    'residential_area': 9,
    'parking_logistics': 5,
    'landmark': 6
}

def is_pin_in_territory(pin_location: Dict[str, float], territory_center: Dict[str, float], radius_meters: float) -> bool:
    """Check if a pin is within territory radius using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    lat1 = radians(pin_location['lat'])
    lon1 = radians(pin_location['lng'])
    lat2 = radians(territory_center['lat'])
    lon2 = radians(territory_center['lng'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # Earth radius in meters
    R = 6371000
    distance = R * c
    
    return distance <= radius_meters

async def calculate_territory_rating(territory_id: str, territory_center: Dict[str, float], radius: float) -> TerritoryRating:
    """Calculate territory rating based on pins within radius"""
    # Get all pins
    pins = await db.pins.find().to_list(length=None)
    
    # Count pins by type within territory
    pin_type_counts = {pin_type: 0 for pin_type in PIN_TYPE_WEIGHTAGES.keys()}
    
    for pin in pins:
        if is_pin_in_territory(pin['location'], territory_center, radius):
            # A pin can have multiple types
            for pin_type in pin.get('type', []):
                if pin_type in pin_type_counts:
                    pin_type_counts[pin_type] += 1
    
    # Calculate scores
    pin_type_scores = {}
    total_score = 0
    
    for pin_type, count in pin_type_counts.items():
        if pin_type in PIN_TYPE_WEIGHTAGES:
            score = PIN_TYPE_WEIGHTAGES[pin_type] * count
            pin_type_scores[pin_type] = score
            total_score += score
    
    # Calculate top contributors (top 3)
    top_contributors = []
    if total_score > 0:
        sorted_scores = sorted(pin_type_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for pin_type, score in sorted_scores:
            if score > 0:
                percentage = (score / total_score) * 100
                top_contributors.append({
                    'type': pin_type.replace('_', ' ').title(),
                    'score': score,
                    'percentage': round(percentage, 2),
                    'count': pin_type_counts[pin_type]
                })
    
    return TerritoryRating(
        totalScore=total_score,
        pinTypeScores=pin_type_scores,
        pinTypeCounts=pin_type_counts,
        topContributors=top_contributors
    )

def calculate_ai_insights(metrics: TerritoryMetrics) -> AIInsights:
    # Check if any data exists
    has_data = any([
        metrics.investments > 0,
        metrics.buildings > 0,
        metrics.populationDensity > 0,
        metrics.qualityOfProject > 0,
        metrics.govtInfra > 0,
        metrics.livabilityIndex > 0,
        metrics.airPollutionIndex > 0,
        metrics.roads > 0,
        metrics.crimeRate > 0
    ])
    
    if not has_data:
        # Return zeros when no data
        return AIInsights(appreciationPercent=0, demandPressure=0, confidenceScore=0, aiSuggestions=["No data available - add metrics to see insights"])
    
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
    
    # Auto-generate zone if not provided
    zone = territory.zone
    if not zone:
        # Generate zone name from pincode (first 3 digits)
        pincode_prefix = territory.pincode[:3]
        zone = f"Zone {pincode_prefix}"
    
    ai_insights = calculate_ai_insights(territory.metrics)
    territory_doc = {
        "id": str(uuid.uuid4()),
        **territory.model_dump(),
        "zone": zone,
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
        
        # Calculate rating on-the-fly if not present or outdated
        if 'rating' not in t or not t.get('rating'):
            rating = await calculate_territory_rating(
                t['id'],
                t['center'],
                t.get('radius', 2500)
            )
            t['rating'] = rating.model_dump()
            # Update in database
            await db.territories.update_one(
                {"id": t['id']},
                {"$set": {"rating": rating.model_dump()}}
            )
        
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

@api_router.post("/territories/{territory_id}/calculate-rating")
async def calculate_territory_rating_endpoint(territory_id: str, user: User = Depends(get_current_user)):
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    if not territory.get('center'):
        raise HTTPException(status_code=400, detail="Territory has no center coordinates")
    
    rating = await calculate_territory_rating(
        territory_id,
        territory['center'],
        territory.get('radius', 2500)
    )
    
    # Update territory with rating
    await db.territories.update_one(
        {"id": territory_id},
        {"$set": {"rating": rating.model_dump(), "updatedAt": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated = await db.territories.find_one({"id": territory_id})
    await manager.broadcast(json.dumps({"type": "territory_updated", "data": updated}))
    
    return {"rating": rating, "message": "Rating calculated successfully"}

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

@api_router.post("/communities")
async def create_community(community: CommunityCreate, user: User = Depends(get_current_user)):
    community_doc = {
        "id": str(uuid.uuid4()),
        **community.model_dump(),
        "createdBy": user.id,
        "members": [user.id],  # Creator is first member
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await db.communities.insert_one(community_doc)
    return Community(**community_doc)

@api_router.get("/communities", response_model=List[Community])
async def get_communities(user: User = Depends(get_current_user)):
    communities = await db.communities.find().to_list(length=None)
    return [Community(**c) for c in communities]

@api_router.get("/communities/{community_id}", response_model=Community)
async def get_community(community_id: str, user: User = Depends(get_current_user)):
    community = await db.communities.find_one({"id": community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return Community(**community)

@api_router.post("/communities/{community_id}/join")
async def join_community(community_id: str, user: User = Depends(get_current_user)):
    community = await db.communities.find_one({"id": community_id})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    
    if user.id not in community.get('members', []):
        await db.communities.update_one(
            {"id": community_id},
            {"$push": {"members": user.id}}
        )
    return {"message": "Joined community successfully"}

@api_router.post("/posts")
async def create_post(post: PostCreate, user: User = Depends(get_current_user)):
    post_doc = {
        "id": str(uuid.uuid4()),
        **post.model_dump(),
        "userId": user.id,
        "userName": user.name,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await db.posts.insert_one(post_doc)
    # Remove MongoDB ObjectId before broadcasting
    broadcast_data = {k: v for k, v in post_doc.items() if k != '_id'}
    await manager.broadcast(json.dumps({"type": "post_created", "data": broadcast_data}))
    return Post(**post_doc)

@api_router.get("/posts", response_model=List[Post])
async def get_posts(user: User = Depends(get_current_user), community_id: Optional[str] = Query(None)):
    query = {}
    if community_id:
        query['communityId'] = community_id
    posts = await db.posts.find(query).sort("createdAt", -1).to_list(length=None)
    return [Post(**p) for p in posts]

@api_router.get("/territories/{territory_id}/profile")
async def get_territory_profile(territory_id: str, user: User = Depends(get_current_user)):
    """Get comprehensive territory profile with all stats"""
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    # Get counts
    professionals_count = await db.professionals.count_documents({"territoryId": territory_id})
    projects_count = await db.projects.count_documents({"territoryId": territory_id})
    opportunities_count = await db.opportunities.count_documents({"territoryId": territory_id})
    posts_count = await db.posts.count_documents({"communityId": {"$in": [c["id"] for c in await db.communities.find({"territoryId": territory_id}).to_list(length=None)]}})
    
    return {
        "territory": Territory(**territory),
        "stats": {
            "professionals": professionals_count,
            "projects": projects_count,
            "opportunities": opportunities_count,
            "posts": posts_count
        }
    }

@api_router.get("/professionals")
async def get_professionals(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None), profession_type: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query["territoryId"] = territory_id
    if profession_type:
        query["professionType"] = profession_type
    professionals = await db.professionals.find(query).to_list(length=None)
    return [Professional(**p) for p in professionals]

@api_router.post("/projects")
async def create_project(project: ProjectCreate, user: User = Depends(get_current_user)):
    project_doc = {
        "id": str(uuid.uuid4()),
        "name": project.name,
        "status": project.status,
        "developerName": project.developerName,
        "priceRange": project.priceRange,
        "configuration": project.configuration,
        "location": project.location,
        "territoryId": project.territoryId,
        "brochureUrl": project.brochureUrl,
        "createdAt": datetime.now(timezone.utc)
    }
    await db.projects.insert_one(project_doc)
    await manager.broadcast(json.dumps({"type": "project_created", "data": {k: v.isoformat() if isinstance(v, datetime) else v for k, v in project_doc.items() if k != '_id'}}))
    return Project(**project_doc)

@api_router.get("/projects")
async def get_projects(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query["territoryId"] = territory_id
    projects = await db.projects.find(query).to_list(length=None)
    return [Project(**p) for p in projects]

@api_router.get("/opportunities")
async def get_opportunities(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query["territoryId"] = territory_id
    opportunities = await db.opportunities.find(query).sort("createdAt", -1).to_list(length=None)
    return [Opportunity(**o) for o in opportunities]

@api_router.post("/events")
async def create_event(event: EventCreate, user: User = Depends(get_current_user)):
    # Parse date string to datetime
    try:
        event_date = datetime.fromisoformat(event.date.replace('Z', '+00:00'))
        # Ensure timezone awareness
        if event_date.tzinfo is None:
            event_date = event_date.replace(tzinfo=timezone.utc)
    except:
        event_date = datetime.now(timezone.utc)
    
    # Determine status based on date
    status = "upcoming" if event_date > datetime.now(timezone.utc) else "past"
    
    event_doc = {
        "id": str(uuid.uuid4()),
        "title": event.title,
        "date": event_date,
        "location": event.location,
        "territoryId": event.territoryId,
        "organizer": event.organizer,
        "status": status,
        "rsvpList": [],
        "createdAt": datetime.now(timezone.utc)
    }
    await db.events.insert_one(event_doc)
    await manager.broadcast(json.dumps({"type": "event_created", "data": {k: v.isoformat() if isinstance(v, datetime) else v for k, v in event_doc.items() if k != '_id'}}))
    return Event(**event_doc)

@api_router.get("/events")
async def get_events(user: User = Depends(get_current_user), territory_id: Optional[str] = Query(None)):
    query = {}
    if territory_id:
        query["territoryId"] = territory_id
    events = await db.events.find(query).to_list(length=None)
    return [Event(**e) for e in events]

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
