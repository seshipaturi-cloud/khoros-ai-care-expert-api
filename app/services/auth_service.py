from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
import secrets
import logging

from app.models.auth import UserInDB, TokenData, UserRegister, UserUpdate
from app.utils import get_database
from config import settings


logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(32)

    def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            email = payload.get("email")
            roles = payload.get("roles", [])
            
            if user_id is None:
                return None
            
            return TokenData(user_id=user_id, email=email, roles=roles)
        except JWTError:
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        db = get_database()
        user = await db.users.find_one({"email": email})
        
        if not user:
            return None
        
        if not self.verify_password(password, user.get("hashed_password", "")):
            return None
        
        user["_id"] = str(user["_id"])
        return UserInDB(**user)

    async def create_user(self, user_data: UserRegister) -> UserInDB:
        db = get_database()
        
        existing_user = await db.users.find_one({
            "$or": [
                {"email": user_data.email},
                {"username": user_data.username}
            ]
        })
        
        if existing_user:
            raise ValueError("User with this email or username already exists")
        
        user_dict = user_data.dict()
        user_dict["hashed_password"] = self.get_password_hash(user_dict.pop("password"))
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        user_dict["is_active"] = True
        user_dict["is_superuser"] = False
        user_dict["last_login"] = None
        
        if not user_dict.get("role_ids"):
            default_role = await db.roles.find_one({"name": "agent"})
            if default_role:
                user_dict["role_ids"] = [str(default_role["_id"])]
            else:
                user_dict["role_ids"] = []
        
        result = await db.users.insert_one(user_dict)
        created_user = await db.users.find_one({"_id": result.inserted_id})
        created_user["_id"] = str(created_user["_id"])
        
        return UserInDB(**created_user)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        db = get_database()
        
        if not ObjectId.is_valid(user_id):
            return None
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        user["_id"] = str(user["_id"])
        return UserInDB(**user)

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        db = get_database()
        user = await db.users.find_one({"email": email})
        
        if not user:
            return None
        
        user["_id"] = str(user["_id"])
        return UserInDB(**user)

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
        db = get_database()
        
        if not ObjectId.is_valid(user_id):
            return None
        
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        
        if "password" in update_data:
            update_data["hashed_password"] = self.get_password_hash(update_data.pop("password"))
        
        if not update_data:
            return await self.get_user_by_id(user_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_user_by_id(user_id)

    async def update_last_login(self, user_id: str):
        db = get_database()
        
        if not ObjectId.is_valid(user_id):
            return
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    async def get_user_roles(self, user_id: str) -> List[dict]:
        db = get_database()
        
        user = await self.get_user_by_id(user_id)
        if not user or not user.role_ids:
            return []
        
        role_object_ids = [ObjectId(role_id) for role_id in user.role_ids if ObjectId.is_valid(role_id)]
        
        roles = []
        async for role in db.roles.find({"_id": {"$in": role_object_ids}}):
            role["_id"] = str(role["_id"])
            roles.append(role)
        
        return roles

    async def check_user_permission(self, user_id: str, permission: str) -> bool:
        roles = await self.get_user_roles(user_id)
        
        for role in roles:
            if permission in role.get("permissions", []):
                return True
        
        return False

    async def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        db = get_database()
        
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "is_active": True
        }
        
        await db.sessions.insert_one(session_data)
        return session_id

    async def validate_session(self, session_id: str) -> Optional[dict]:
        db = get_database()
        
        session = await db.sessions.find_one({
            "session_id": session_id,
            "is_active": True
        })
        
        if not session:
            return None
        
        session_age = (datetime.utcnow() - session["created_at"]).total_seconds()
        if session_age > 86400:  # 24 hours
            await self.invalidate_session(session_id)
            return None
        
        await db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )
        
        return session

    async def invalidate_session(self, session_id: str):
        db = get_database()
        
        await db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"is_active": False}}
        )

    async def invalidate_all_user_sessions(self, user_id: str):
        db = get_database()
        
        await db.sessions.update_many(
            {"user_id": user_id, "is_active": True},
            {"$set": {"is_active": False}}
        )


auth_service = AuthService()