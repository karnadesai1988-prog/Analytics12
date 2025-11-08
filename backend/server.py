from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

# OpenAI client (optional - can be configured per request)
openai_client = None
if os.environ.get('OPENAI_API_KEY'):
    openai_client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Create the main app
app = FastAPI(title="R Territory AI Engine")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket manager for real-time sync
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

class Territory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    city: str
    zone: str
    center: Dict[str, float]  # {"lat": 28.6139, "lng": 77.2090}
    radius: float = 3000  # 3km radius in meters
    metrics: TerritoryMetrics
    restrictions: TerritoryRestrictions
    aiInsights: AIInsights
    createdBy: str
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TerritoryCreate(BaseModel):
    name: str
    city: str
    zone: str
    center: Dict[str, float]
    radius: float = 3000
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

# Event/Pin Models
class EventPin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    title: str
    description: str
    location: Dict[str, float]  # {"lat": x, "lng": y}
    category: str  # "social", "infrastructure", "event", "issue"
    mediaUrls: List[str] = []
    socialShare: bool = True
    createdBy: str
    userName: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventPinCreate(BaseModel):
    territoryId: str
    title: str
    description: str
    location: Dict[str, float]
    category: str
    socialShare: bool = True

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
        
        return AIInsights(
            appreciationPercent=round(max(0, min(appreciation, 25)), 2),
            demandPressure=round(max(0, demand_pressure), 2),
            confidenceScore=round(confidence, 2)
        )
    except Exception as e:
        logging.error(f"Error in predict_appreciation: {e}")
        return AIInsights(appreciationPercent=0, demandPressure=0, confidenceScore=0.5)

def validate_comment_regex(text: str) -> Dict:
    banned_patterns = [
        r'spam', r'fake', r'free\s+money', r'abuse', r'offensive',
        r'click\s+here', r'buy\s+now', r'urgent', r'winner'
    ]
    
    for pattern in banned_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"label": "flagged", "reason": f"Matched banned pattern: {pattern}"}
    
    return {"label": "valid", "reason": "No violations detected"}

async def validate_comment_ai(text: str, api_key: str) -> Dict:
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a content moderator. Analyze comments and determine if they contain spam, abuse, offensive language, or inappropriate content. Respond with only 'VALID' or 'FLAGGED: reason'."},
                {"role": "user", "content": f"Analyze this comment: {text}"}
            ],
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        
        if "FLAGGED" in result:
            reason = result.replace("FLAGGED:", "").strip()
            return {"label": "flagged", "reason": reason}
        else:
            return {"label": "valid", "reason": "AI validation passed"}
    except Exception as e:
        logging.error(f"AI validation error: {e}")
        return {"label": "valid", "reason": f"AI validation unavailable: {str(e)}"}

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserRegister):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    
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
async def configure_api_key(
    config: APIKeyConfig,
    current_user: Dict = Depends(get_current_user)
):
    await db.users.update_one(
        {"id": current_user['user_id']},
        {"$set": {"openai_api_key": config.openai_api_key}}
    )
    return {"message": "API key configured successfully"}

# ==================== TERRITORY ROUTES ====================

@api_router.post("/territories", response_model=Territory)
async def create_territory(
    territory_data: TerritoryCreate,
    current_user: Dict = Depends(get_current_user)
):
    ai_insights = predict_appreciation(territory_data.metrics)
    
    territory = Territory(
        name=territory_data.name,
        city=territory_data.city,
        zone=territory_data.zone,
        center=territory_data.center,
        radius=territory_data.radius,
        metrics=territory_data.metrics,
        restrictions=territory_data.restrictions,
        aiInsights=ai_insights,
        createdBy=current_user['user_id']
    )
    
    doc = territory.model_dump()
    doc['updatedAt'] = doc['updatedAt'].isoformat()
    
    await db.territories.insert_one(doc)
    
    history = MetricsHistory(
        territoryId=territory.id,
        metrics=territory.metrics,
        aiInsights=ai_insights
    )
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
    
    return territories

@api_router.get("/territories/{territory_id}", response_model=Territory)
async def get_territory(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    territory = await db.territories.find_one({"id": territory_id}, {"_id": 0})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    if isinstance(territory.get('updatedAt'), str):
        territory['updatedAt'] = datetime.fromisoformat(territory['updatedAt'])
    
    return Territory(**territory)

@api_router.put("/territories/{territory_id}", response_model=Territory)
async def update_territory(
    territory_id: str,
    territory_data: TerritoryUpdate,
    current_user: Dict = Depends(get_current_user)
):
    if current_user['role'] not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    existing = await db.territories.find_one({"id": territory_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    update_data = territory_data.model_dump(exclude_none=True)
    
    if 'metrics' in update_data:
        metrics = TerritoryMetrics(**update_data['metrics'])
        ai_insights = predict_appreciation(metrics)
        update_data['aiInsights'] = ai_insights.model_dump()
    
    update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    
    await db.territories.update_one(
        {"id": territory_id},
        {"$set": update_data}
    )
    
    if 'metrics' in update_data:
        history = MetricsHistory(
            territoryId=territory_id,
            metrics=metrics,
            aiInsights=ai_insights
        )
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
async def delete_territory(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    if current_user['role'] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete territories")
    
    result = await db.territories.delete_one({"id": territory_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    await manager.broadcast(json.dumps({"type": "territory_deleted", "territoryId": territory_id}))
    
    return {"message": "Territory deleted successfully"}

# ==================== EVENT PIN ROUTES ====================

@api_router.post("/events", response_model=EventPin)
async def create_event(
    event_data: EventPinCreate,
    current_user: Dict = Depends(get_current_user)
):
    user = await db.users.find_one({"id": current_user['user_id']})
    
    event = EventPin(
        territoryId=event_data.territoryId,
        title=event_data.title,
        description=event_data.description,
        location=event_data.location,
        category=event_data.category,
        socialShare=event_data.socialShare,
        createdBy=current_user['user_id'],
        userName=user['name']
    )
    
    doc = event.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    
    await db.events.insert_one(doc)
    
    await manager.broadcast(json.dumps({"type": "event_created", "data": doc}))
    
    return event

@api_router.get("/events/{territory_id}", response_model=List[EventPin])
async def get_events(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    events = await db.events.find(
        {"territoryId": territory_id},
        {"_id": 0}
    ).sort("createdAt", -1).to_list(100)
    
    for event in events:
        if isinstance(event.get('createdAt'), str):
            event['createdAt'] = datetime.fromisoformat(event['createdAt'])
    
    return events

@api_router.get("/events", response_model=List[EventPin])
async def get_all_events(current_user: Dict = Depends(get_current_user)):
    events = await db.events.find({}, {"_id": 0}).sort("createdAt", -1).to_list(1000)
    
    for event in events:
        if isinstance(event.get('createdAt'), str):
            event['createdAt'] = datetime.fromisoformat(event['createdAt'])
    
    return events

# ==================== SHARE LINK ROUTES ====================

@api_router.post("/share-links")
async def create_share_link(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    share_link = ShareLink(
        territoryId=territory_id,
        createdBy=current_user['user_id']
    )
    
    doc = share_link.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    doc['expiresAt'] = doc['expiresAt'].isoformat()
    
    await db.share_links.insert_one(doc)
    
    return {
        "shareToken": share_link.token,
        "shareUrl": f"/share/{share_link.token}",
        "expiresAt": share_link.expiresAt
    }

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
    
    return {
        "territory": Territory(**territory),
        "token": token
    }

# ==================== COMMENT ROUTES ====================

@api_router.post("/comments", response_model=Comment)
async def create_comment(
    comment_data: CommentCreate,
    current_user: Dict = Depends(get_current_user)
):
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
        territoryId=comment_data.territoryId,
        userId=current_user['user_id'],
        userName=user['name'],
        text=comment_data.text,
        validationStatus=validation['label'],
        validationReason=validation['reason']
    )
    
    doc = comment.model_dump()
    doc['createdAt'] = doc['createdAt'].isoformat()
    
    await db.comments.insert_one(doc)
    return comment

@api_router.get("/comments/{territory_id}", response_model=List[Comment])
async def get_comments(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    comments = await db.comments.find(
        {"territoryId": territory_id},
        {"_id": 0}
    ).sort("createdAt", -1).to_list(100)
    
    for comment in comments:
        if isinstance(comment.get('createdAt'), str):
            comment['createdAt'] = datetime.fromisoformat(comment['createdAt'])
    
    return comments

# ==================== DATA GATHERING ROUTES ====================

@api_router.post("/data-gathering", response_model=DataGathering)
async def submit_data(
    form_data: DataGatheringForm,
    current_user: Dict = Depends(get_current_user)
):
    data_entry = DataGathering(
        territoryId=form_data.territoryId,
        data=form_data.data,
        submittedBy=current_user['user_id'],
        shareToken=form_data.shareToken
    )
    
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.data_gathering.insert_one(doc)
    
    await manager.broadcast(json.dumps({"type": "data_submitted", "territoryId": form_data.territoryId}))
    
    return data_entry

@api_router.post("/data-gathering/public")
async def submit_data_public(form_data: dict):
    """Public endpoint for shared link data submission"""
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
        territoryId=link['territoryId'],
        data=form_data.get('data', {}),
        submittedBy="anonymous",
        shareToken=share_token
    )
    
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.data_gathering.insert_one(doc)
    
    await manager.broadcast(json.dumps({"type": "data_submitted", "territoryId": link['territoryId']}))
    
    return {"message": "Data submitted successfully", "id": data_entry.id}

@api_router.get("/data-gathering/{territory_id}", response_model=List[DataGathering])
async def get_data_gathering(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    data = await db.data_gathering.find(
        {"territoryId": territory_id},
        {"_id": 0}
    ).to_list(1000)
    
    for entry in data:
        if isinstance(entry.get('timestamp'), str):
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
    
    return data

# ==================== METRICS HISTORY ROUTES ====================

@api_router.get("/metrics-history/{territory_id}", response_model=List[MetricsHistory])
async def get_metrics_history(
    territory_id: str,
    current_user: Dict = Depends(get_current_user)
):
    history = await db.metrics_history.find(
        {"territoryId": territory_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for entry in history:
        if isinstance(entry.get('timestamp'), str):
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
    
    return history

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
    return {"message": "R Territory AI Predictive Insights Engine API", "version": "2.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()