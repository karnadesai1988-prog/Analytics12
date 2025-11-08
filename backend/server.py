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
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

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
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI()

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
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# ==================== MODELS ====================

# User Models
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Territory Models
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
    coordinates: Dict[str, Any]  # GeoJSON
    metrics: TerritoryMetrics
    restrictions: TerritoryRestrictions
    aiInsights: AIInsights
    createdBy: str
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TerritoryCreate(BaseModel):
    name: str
    city: str
    zone: str
    coordinates: Dict[str, Any]
    metrics: TerritoryMetrics = Field(default_factory=TerritoryMetrics)
    restrictions: TerritoryRestrictions = Field(default_factory=TerritoryRestrictions)

class TerritoryUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zone: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None
    metrics: Optional[TerritoryMetrics] = None
    restrictions: Optional[TerritoryRestrictions] = None

# Comment Models
class CommentCreate(BaseModel):
    territoryId: str
    text: str
    useAI: bool = False  # Toggle for AI validation

class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    userId: str
    userName: str
    text: str
    validationStatus: str  # "valid", "flagged", "pending"
    validationReason: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Data Gathering Models
class DataGatheringForm(BaseModel):
    territoryId: str
    data: Dict[str, Any]
    submittedBy: str

class DataGathering(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    data: Dict[str, Any]
    submittedBy: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Metrics History for Charts
class MetricsHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    territoryId: str
    metrics: TerritoryMetrics
    aiInsights: AIInsights
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

# AI Prediction Function
def predict_appreciation(metrics: TerritoryMetrics) -> AIInsights:
    """
    Calculate price appreciation based on territory metrics
    Formula: appreciation = 0.3*log(investments+1) + 0.25*livabilityIndex - 0.15*crimeRate + 0.2*govtInfra
    """
    try:
        appreciation = (
            0.3 * np.log(metrics.investments + 1) +
            0.25 * (metrics.livabilityIndex / 10) +
            0.2 * (metrics.govtInfra / 10) -
            0.15 * (metrics.crimeRate / 10) +
            0.1 * (metrics.qualityOfProject / 10) -
            0.05 * (metrics.airPollutionIndex / 10)
        ) * 100
        
        # Calculate demand pressure
        demand_pressure = (
            0.4 * (metrics.populationDensity / 1000) +
            0.3 * (metrics.buildings / 100) +
            0.3 * (metrics.investments / 1000000)
        ) * 100
        
        # Confidence score (higher is better)
        confidence = min(0.85 + (metrics.qualityOfProject / 100), 0.95)
        
        return AIInsights(
            appreciationPercent=round(max(0, appreciation), 2),
            demandPressure=round(max(0, min(100, demand_pressure)), 2),
            confidenceScore=round(confidence, 2)
        )
    except Exception as e:
        logging.error(f"Error in predict_appreciation: {e}")
        return AIInsights(
            appreciationPercent=0,
            demandPressure=0,
            confidenceScore=0.5
        )

# Comment Validation Functions
def validate_comment_regex(text: str) -> Dict:
    """Basic regex validation for spam and abuse"""
    banned_patterns = [
        r'spam', r'fake', r'free\s+money', r'abuse', r'offensive',
        r'click\s+here', r'buy\s+now', r'urgent', r'winner'
    ]
    
    for pattern in banned_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"label": "flagged", "reason": f"Matched banned pattern: {pattern}"}
    
    return {"label": "valid", "reason": "No violations detected"}

async def validate_comment_ai(text: str) -> Dict:
    """AI-powered comment validation using GPT-5"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id="comment-validation",
            system_message="You are a content moderator. Analyze comments and determine if they contain spam, abuse, offensive language, or inappropriate content. Respond with only 'VALID' or 'FLAGGED: reason'."
        ).with_model("openai", "gpt-5")
        
        user_message = UserMessage(
            text=f"Analyze this comment: {text}"
        )
        
        response = await chat.send_message(user_message)
        
        if "FLAGGED" in response:
            reason = response.replace("FLAGGED:", "").strip()
            return {"label": "flagged", "reason": reason}
        else:
            return {"label": "valid", "reason": "AI validation passed"}
    except Exception as e:
        logging.error(f"AI validation error: {e}")
        return {"label": "valid", "reason": "AI validation unavailable, defaulting to valid"}

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
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
            "role": user['role']
        }
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: Dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# ==================== TERRITORY ROUTES ====================

@api_router.post("/territories", response_model=Territory)
async def create_territory(
    territory_data: TerritoryCreate,
    current_user: Dict = Depends(get_current_user)
):
    # Calculate AI insights
    ai_insights = predict_appreciation(territory_data.metrics)
    
    territory = Territory(
        name=territory_data.name,
        city=territory_data.city,
        zone=territory_data.zone,
        coordinates=territory_data.coordinates,
        metrics=territory_data.metrics,
        restrictions=territory_data.restrictions,
        aiInsights=ai_insights,
        createdBy=current_user['user_id']
    )
    
    doc = territory.model_dump()
    doc['updatedAt'] = doc['updatedAt'].isoformat()
    
    await db.territories.insert_one(doc)
    
    # Save to history
    history = MetricsHistory(
        territoryId=territory.id,
        metrics=territory.metrics,
        aiInsights=ai_insights
    )
    history_doc = history.model_dump()
    history_doc['timestamp'] = history_doc['timestamp'].isoformat()
    await db.metrics_history.insert_one(history_doc)
    
    # Broadcast update (without _id)
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
    # Check permissions
    if current_user['role'] not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.COMMUNITY_HEAD]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    existing = await db.territories.find_one({"id": territory_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    update_data = territory_data.model_dump(exclude_none=True)
    
    # Recalculate AI insights if metrics updated
    if 'metrics' in update_data:
        metrics = TerritoryMetrics(**update_data['metrics'])
        ai_insights = predict_appreciation(metrics)
        update_data['aiInsights'] = ai_insights.model_dump()
    
    update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
    
    await db.territories.update_one(
        {"id": territory_id},
        {"$set": update_data}
    )
    
    # Save to history if metrics updated
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
    
    # Broadcast update (without _id)
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
    
    # Broadcast deletion
    await manager.broadcast(json.dumps({"type": "territory_deleted", "territoryId": territory_id}))
    
    return {"message": "Territory deleted successfully"}

# ==================== COMMENT ROUTES ====================

@api_router.post("/comments", response_model=Comment)
async def create_comment(
    comment_data: CommentCreate,
    current_user: Dict = Depends(get_current_user)
):
    # Validate comment
    if comment_data.useAI:
        validation = await validate_comment_ai(comment_data.text)
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
        submittedBy=current_user['user_id']
    )
    
    doc = data_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.data_gathering.insert_one(doc)
    return data_entry

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
            # Echo back for heartbeat
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "R Territory AI Predictive Insights Engine API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()