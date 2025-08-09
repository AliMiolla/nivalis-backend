from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel
import os
import uuid
import json
import base64
from typing import Optional, List
import requests
from datetime import datetime, timedelta
import hashlib
import hmac
from io import BytesIO

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb+srv://nivalis_admin:NiVALiS2025@nivalis.x55b73u.mongodb.net/?retryWrites=true&w=majority&appName=Nivalis')

try:
    client = MongoClient(MONGO_URL)
    db = client.nival
    print(f"Connected to MongoDB at {MONGO_URL}")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

app = FastAPI(title="NiVALiS Real Estate API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Property(BaseModel):
    id: Optional[str] = None
    title_tr: str
    title_en: str
    title_ar: Optional[str] = None
    title_ru: Optional[str] = None
    description_tr: str
    description_en: str
    description_ar: Optional[str] = None
    description_ru: Optional[str] = None
    price: float
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bedrooms: int
    bathrooms: int
    size: float
    property_type: str
    image_url: str
    images: List[str] = []
    video: Optional[str] = None
    features_tr: List[str] = []
    features_en: List[str] = []
    rooms: Optional[int] = None
    status: str = 'sale'
    featured: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AboutContent(BaseModel):
    id: Optional[str] = None
    content_tr: str
    content_en: str
    content_ar: Optional[str] = None
    content_ru: Optional[str] = None
    updated_at: Optional[datetime] = None

class NewsletterSubscription(BaseModel):
    email: str
    subscribed_at: Optional[datetime] = None

class BlogPost(BaseModel):
    id: Optional[str] = None
    title_tr: str
    title_en: str
    content_tr: str
    content_en: str
    created_at: Optional[datetime] = None

class User(BaseModel):
    id: Optional[str] = None
    email: str
    name: str
    picture: Optional[str] = None
    created_at: Optional[datetime] = None

class UserSession(BaseModel):
    id: Optional[str] = None
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: Optional[datetime] = None

class FooterContent(BaseModel):
    id: Optional[str] = None
    company_description_tr: str
    company_description_en: str
    company_description_ar: Optional[str] = None
    company_description_ru: Optional[str] = None
    address: str
    phone: str
    email: str
    updated_at: Optional[datetime] = None

# Initialize collections
properties = db.properties
about_content = db.about_content
footer_content = db.footer_content
newsletter = db.newsletter
blog_posts = db.blog_posts
users = db.users
user_sessions = db.user_sessions

@app.get("/")
def read_root():
    return {"message": "NiVALiS Real Estate API"}

# About Content endpoints
@app.get("/api/about")
def get_about_content():
    try:
        content = about_content.find_one()
        if content:
            content['id'] = str(content['_id'])
            del content['_id']
            return content
        else:
            # Return default content if none exists
            default_content = {
                "content_tr": "NiVALiS İnşaat Gayrimenkul olarak, sektördeki uzun yıllık deneyimimiz ve profesyonel ekibimizle müşterilerimize en kaliteli hizmeti sunmayı hedefliyoruz. Türkiye'nin önde gelen gayrimenkul şirketlerinden biri olarak, konut, ticari gayrimenkul ve yatırım danışmanlığı konularında uzmanlaşmış durumdayız.",
                "content_en": "As NiVALiS Construction Real Estate, we aim to provide the highest quality service to our customers with our many years of experience in the sector and our professional team. As one of Turkey's leading real estate companies, we specialize in residential, commercial real estate and investment consultancy."
            }
            return default_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/about")
def update_about_content(content: AboutContent):
    try:
        content_dict = content.dict()
        content_dict['updated_at'] = datetime.now()
        
        # Update or insert
        result = about_content.replace_one(
            {},
            content_dict,
            upsert=True
        )
        
        return {"message": "About content updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Footer Content endpoints
@app.get("/api/footer")
def get_footer_content():
    try:
        content = footer_content.find_one()
        if content:
            content['id'] = str(content['_id'])
            del content['_id']
            return content
        else:
            # Return default footer content if none exists
            default_content = {
                "company_description_tr": "Türkiye'nin önde gelen gayrimenkul şirketi olarak sizlere hizmet veriyoruz.",
                "company_description_en": "As one of Turkey's leading real estate companies, we serve you.",
                "company_description_ar": "نحن نخدمكم كشركة عقارية رائدة في تركيا.",
                "company_description_ru": "Мы обслуживаем вас как ведущая турецкая компания недвижимости.",
                "address": "Merkez Mah. Albay Burak Cad.\nTaşkan Sezgin İş Hanı No:8\nKat:2/13 Gölcük / Kocaeli",
                "phone": "+90 (532) 371 81 28",
                "email": "info@nivalisinsaat.com"
            }
            return default_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/footer")
def update_footer_content(content: FooterContent):
    try:
        content_dict = content.dict()
        content_dict['updated_at'] = datetime.now()
        
        # Update or insert
        result = footer_content.replace_one(
            {},
            content_dict,
            upsert=True
        )
        
        return {"message": "Footer content updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Properties endpoints
@app.post("/api/create-test-admin")
async def create_test_admin():
    """Create test admin user for testing purposes - DEVELOPMENT ONLY"""
    try:
        # Create test admin user
        test_user = {
            "id": str(uuid.uuid4()),
            "email": "test@admin.com",
            "name": "Test Admin User",
            "picture": None,
            "created_at": datetime.now()
        }
        
        # Check if user already exists
        existing = users.find_one({"email": "test@admin.com"})
        if existing:
            user_id = existing["id"]
        else:
            users.insert_one(test_user)
            user_id = test_user["id"]
        
        # Create session token
        session_token = f"test-admin-session-{uuid.uuid4()}"
        expires_at = datetime.now() + timedelta(days=7)
        
        # Remove old sessions
        user_sessions.delete_many({"user_id": user_id})
        
        # Create new session
        new_session = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        user_sessions.insert_one(new_session)
        
        return {
            "message": "Test admin created successfully",
            "user": {
                "id": user_id,
                "email": "test@admin.com",
                "name": "Test Admin User",
                "is_admin": True
            },
            "session_token": session_token,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties")
def get_properties(featured: Optional[bool] = None, status: Optional[str] = None, limit: Optional[int] = None):
    try:
        query = {}
        if featured is not None:
            query['featured'] = featured
        if status is not None:
            query['status'] = status
            
        cursor = properties.find(query)
        if limit:
            cursor = cursor.limit(limit)
            
        properties_list = []
        for prop in cursor:
            # Keep the custom id field if it exists, otherwise use MongoDB _id
            if 'id' not in prop:
                prop['id'] = str(prop['_id'])
            del prop['_id']
            properties_list.append(prop)
            
        return properties_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/{property_id}")
def get_property_by_id(property_id: str):
    try:
        # Try to find by ObjectId first
        try:
            prop = properties.find_one({"_id": ObjectId(property_id)})
        except:
            # If ObjectId conversion fails, try to find by id field
            prop = properties.find_one({"id": property_id})
            
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
            
        # Keep the custom id field if it exists, otherwise use MongoDB _id
        if 'id' not in prop:
            prop['id'] = str(prop['_id'])
        del prop['_id']
        return prop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/properties")
def create_property(property_data: Property):
    try:
        property_dict = property_data.dict()
        property_dict['id'] = str(uuid.uuid4())
        property_dict['created_at'] = datetime.now()
        
        result = properties.insert_one(property_dict)
        property_dict['_id'] = str(result.inserted_id)
        
        return {"message": "Property created successfully", "id": property_dict['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Newsletter endpoints
@app.post("/api/newsletter/subscribe")
def subscribe_newsletter(subscription: NewsletterSubscription):
    try:
        # Check if email already exists
        existing = newsletter.find_one({"email": subscription.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already subscribed")
            
        subscription_dict = subscription.dict()
        subscription_dict['subscribed_at'] = datetime.now()
        
        result = newsletter.insert_one(subscription_dict)
        return {"message": "Successfully subscribed to newsletter"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Blog posts endpoints  
@app.get("/api/blog-posts")
def get_blog_posts(limit: Optional[int] = 5):
    try:
        cursor = blog_posts.find().sort("created_at", -1)
        if limit:
            cursor = cursor.limit(limit)
            
        posts_list = []
        for post in cursor:
            post['id'] = str(post['_id'])
            del post['_id']
            posts_list.append(post)
            
        return posts_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/blog-posts")
def create_blog_post(post: BlogPost):
    try:
        post_dict = post.dict()
        post_dict['id'] = str(uuid.uuid4())
        post_dict['created_at'] = datetime.now()
        
        result = blog_posts.insert_one(post_dict)
        return {"message": "Blog post created successfully", "id": post_dict['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Logo upload endpoint
@app.post("/api/admin/upload-logo")
async def upload_logo(request: Request):
    try:
        form = await request.form()
        logo_file = form.get("logo")
        
        if not logo_file:
            raise HTTPException(status_code=400, detail="No logo file provided")
        
        # Read the file content
        file_content = await logo_file.read()
        
        # Convert to base64 for storage
        import base64
        logo_base64 = base64.b64encode(file_content).decode('utf-8')
        file_extension = logo_file.filename.split('.')[-1].lower()
        
        # Store in database
        logo_data = {
            "logo_base64": logo_base64,
            "file_extension": file_extension,
            "filename": logo_file.filename,
            "uploaded_at": datetime.now()
        }
        
        # Update or insert logo
        result = db.site_settings.replace_one(
            {"type": "logo"},
            {"type": "logo", **logo_data},
            upsert=True
        )
        
        return {"message": "Logo uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logo")
def get_logo():
    try:
        logo_data = db.site_settings.find_one({"type": "logo"})
        if logo_data:
            return {
                "logo_base64": logo_data["logo_base64"],
                "file_extension": logo_data["file_extension"],
                "filename": logo_data["filename"]
            }
        return {"message": "No logo found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/header-logo")
def get_header_logo():
    try:
        header_logo_data = db.site_settings.find_one({"type": "header_logo"})
        if header_logo_data:
            return {
                "logo_base64": header_logo_data["logo_base64"],
                "file_extension": header_logo_data["file_extension"],
                "filename": header_logo_data["filename"]
            }
        # Fallback to regular logo if no header logo exists
        logo_data = db.site_settings.find_one({"type": "logo"})
        if logo_data:
            return {
                "logo_base64": logo_data["logo_base64"],
                "file_extension": logo_data["file_extension"],
                "filename": logo_data["filename"]
            }
        return {"message": "No header logo found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Authentication endpoints
@app.post("/api/auth/profile")
async def get_user_profile(request: Request):
    """Get user profile from Emergent auth API using session ID"""
    try:
        # Get session ID from headers
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Call Emergent auth API
        auth_response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user_data = auth_response.json()
        
        # Check if user exists, if not create new user
        existing_user = users.find_one({"email": user_data["email"]})
        if not existing_user:
            new_user = {
                "id": str(uuid.uuid4()),
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data.get("picture"),
                "created_at": datetime.now()
            }
            users.insert_one(new_user)
            user_id = new_user["id"]
        else:
            user_id = existing_user["id"]
        
        # Create or update session token (7 days expiry)
        session_token = user_data["session_token"]
        expires_at = datetime.now() + timedelta(days=7)
        
        # Remove old sessions for this user
        user_sessions.delete_many({"user_id": user_id})
        
        # Create new session
        new_session = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        user_sessions.insert_one(new_session)
        
        # Check if user is admin
        admin_emails = ["ali.miolla61@gmail.com", "test@admin.com", "admin@test.com"]
        is_admin = user_data["email"] in admin_emails
        
        return {
            "user": {
                "id": user_id,
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data.get("picture"),
                "is_admin": is_admin
            },
            "session_token": session_token,
            "expires_at": expires_at.isoformat()
        }
        
    except requests.RequestException:
        raise HTTPException(status_code=401, detail="Authentication service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/verify")
async def verify_session(request: Request):
    """Verify if session token is valid"""
    try:
        # Get session token from headers or cookies
        session_token = request.headers.get("Authorization")
        if session_token and session_token.startswith("Bearer "):
            session_token = session_token[7:]
        
        if not session_token:
            raise HTTPException(status_code=401, detail="No session token provided")
        
        # Check if session exists and is not expired
        session = user_sessions.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now()}
        })
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Get user data
        user = users.find_one({"id": session["user_id"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Check if user is admin
        admin_emails = ["ali.miolla61@gmail.com", "test@admin.com", "admin@test.com"]
        is_admin = user["email"] in admin_emails
        
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "picture": user.get("picture"),
                "is_admin": is_admin
            },
            "valid": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user by invalidating session token"""
    try:
        # Get session token
        session_token = request.headers.get("Authorization")
        if session_token and session_token.startswith("Bearer "):
            session_token = session_token[7:]
        
        if session_token:
            # Delete the session
            user_sessions.delete_one({"session_token": session_token})
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin-only property management endpoints
@app.post("/api/admin/properties")
async def create_property(property_data: dict, request: Request):
    """Create new property - Admin only"""
    try:
        # Verify admin session
        session_token = request.headers.get("Authorization")
        if session_token and session_token.startswith("Bearer "):
            session_token = session_token[7:]
        
        if not session_token:
            raise HTTPException(status_code=401, detail="No session token provided")
        
        # Check if session exists and get user
        session = user_sessions.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now()}
        })
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        user = users.find_one({"id": session["user_id"]})
        admin_emails = ["ali.miolla61@gmail.com", "test@admin.com", "admin@test.com"]
        if not user or user["email"] not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Create property
        new_property = {
            "id": str(uuid.uuid4()),
            "title_tr": property_data["title_tr"],
            "title_en": property_data["title_en"],
            "title_ar": property_data.get("title_ar"),
            "title_ru": property_data.get("title_ru"),
            "description_tr": property_data["description_tr"],
            "description_en": property_data["description_en"],
            "description_ar": property_data.get("description_ar"),
            "description_ru": property_data.get("description_ru"),
            "price": property_data["price"],
            "location": property_data["location"],
            "latitude": property_data.get("latitude"),
            "longitude": property_data.get("longitude"),
            "size": property_data["size"],
            "rooms": property_data["rooms"],
            "bathrooms": property_data["bathrooms"],
            "property_type": property_data["property_type"],
            "status": property_data["status"],
            "featured": property_data.get("featured", False),
            "images": property_data.get("images", []),
            "video": property_data.get("video"),
            "features_tr": property_data.get("features_tr", []),
            "features_en": property_data.get("features_en", []),
            "created_at": datetime.now()
        }
        
        # Validate document size before saving
        property_json = json.dumps(new_property, default=str)
        document_size = len(property_json.encode('utf-8'))
        
        # MongoDB BSON limit is 16MB - we need to be more restrictive
        practical_limit = 12 * 1024 * 1024  # 12MB practical limit for safety
        bson_limit = 16 * 1024 * 1024  # MongoDB's actual BSON limit
        
        print(f"🔍 Document size check: {document_size} bytes ({document_size/1024/1024:.2f}MB)")
        
        if document_size > bson_limit:
            # Document too large for MongoDB
            raise HTTPException(
                status_code=413,
                detail=f"İlan verisi çok büyük ({document_size/1024/1024:.1f}MB). MongoDB limit: 16MB. Lütfen video boyutunu küçültün (max 8-10MB önerili) veya daha az resim kullanın."
            )
        elif document_size > practical_limit:
            # Warn about approaching limit but try to save
            print(f"⚠️ WARNING: Document size ({document_size/1024/1024:.2f}MB) is close to MongoDB limit")
            
        try:
            result = properties.insert_one(new_property)
            if result.inserted_id:
                print(f"✅ Property saved successfully: {result.inserted_id}")
            else:
                raise HTTPException(status_code=500, detail="Failed to save property")
        except Exception as mongo_error:
            error_message = str(mongo_error)
            print(f"❌ MongoDB Error: {error_message}")
            
            if "too large" in error_message.lower() or "bson" in error_message.lower():
                raise HTTPException(
                    status_code=413,
                    detail=f"Video/resim dosyaları çok büyük. MongoDB 16MB sınırı aşıldı. Çözüm: Video boyutunu 8-10MB altına düşürün veya daha az resim kullanın."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Database error: {error_message}")
        return {"message": "Property created successfully", "id": new_property["id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/properties/{property_id}")
async def update_property(property_id: str, property_data: dict, request: Request):
    """Update property - Admin only"""
    try:
        # Verify admin session
        session_token = request.headers.get("Authorization")
        if session_token and session_token.startswith("Bearer "):
            session_token = session_token[7:]
        
        if not session_token:
            raise HTTPException(status_code=401, detail="No session token provided")
        
        session = user_sessions.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now()}
        })
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        user = users.find_one({"id": session["user_id"]})
        admin_emails = ["ali.miolla61@gmail.com", "test@admin.com", "admin@test.com"]
        if not user or user["email"] not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Update property
        update_data = {
            "title_tr": property_data["title_tr"],
            "title_en": property_data["title_en"],
            "title_ar": property_data.get("title_ar"),
            "title_ru": property_data.get("title_ru"),
            "description_tr": property_data["description_tr"],
            "description_en": property_data["description_en"],
            "description_ar": property_data.get("description_ar"),
            "description_ru": property_data.get("description_ru"),
            "price": property_data["price"],
            "location": property_data["location"],
            "latitude": property_data.get("latitude"),
            "longitude": property_data.get("longitude"),
            "size": property_data["size"],
            "rooms": property_data["rooms"],
            "bathrooms": property_data["bathrooms"],
            "property_type": property_data["property_type"],
            "status": property_data["status"],
            "featured": property_data.get("featured", False),
            "images": property_data.get("images", []),
            "video": property_data.get("video"),
            "features_tr": property_data.get("features_tr", []),
            "features_en": property_data.get("features_en", []),
            "updated_at": datetime.now()
        }
        
        # Validate document size before saving
        property_json = json.dumps(update_data, default=str)
        document_size = len(property_json.encode('utf-8'))
        
        # MongoDB BSON limit is 16MB - we need to be more restrictive
        practical_limit = 12 * 1024 * 1024  # 12MB practical limit for safety
        bson_limit = 16 * 1024 * 1024  # MongoDB's actual BSON limit
        
        print(f"🔍 Document size check: {document_size} bytes ({document_size/1024/1024:.2f}MB)")
        
        if document_size > bson_limit:
            # Document too large for MongoDB
            raise HTTPException(
                status_code=413,
                detail=f"İlan verisi çok büyük ({document_size/1024/1024:.1f}MB). MongoDB limit: 16MB. Lütfen video boyutunu küçültün (max 8-10MB önerili) veya daha az resim kullanın."
            )
        elif document_size > practical_limit:
            # Warn about approaching limit but try to save
            print(f"⚠️ WARNING: Document size ({document_size/1024/1024:.2f}MB) is close to MongoDB limit")
            
        try:
            result = properties.update_one({"id": property_id}, {"$set": update_data})
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Property not found")
            print(f"✅ Property updated successfully")
        except Exception as mongo_error:
            error_message = str(mongo_error)
            print(f"❌ MongoDB Error: {error_message}")
            
            if "too large" in error_message.lower() or "bson" in error_message.lower():
                raise HTTPException(
                    status_code=413,
                    detail=f"Video/resim dosyaları çok büyük. MongoDB 16MB sınırı aşıldı. Çözüm: Video boyutunu 8-10MB altına düşürün veya daha az resim kullanın."
                )
            elif result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Property not found")
            else:
                raise HTTPException(status_code=500, detail=f"Database error: {error_message}")
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {"message": "Property updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/properties/{property_id}")
async def delete_property(property_id: str, request: Request):
    """Delete property - Admin only"""
    try:
        # Verify admin session
        session_token = request.headers.get("Authorization")
        if session_token and session_token.startswith("Bearer "):
            session_token = session_token[7:]
        
        if not session_token:
            raise HTTPException(status_code=401, detail="No session token provided")
        
        session = user_sessions.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now()}
        })
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        user = users.find_one({"id": session["user_id"]})
        admin_emails = ["ali.miolla61@gmail.com", "test@admin.com", "admin@test.com"]
        if not user or user["email"] not in admin_emails:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Delete property
        result = properties.delete_one({"id": property_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {"message": "Property deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/search")
def search_properties(
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    property_type: Optional[str] = None,
    bedrooms: Optional[int] = None
):
    try:
        query = {}
        
        if location:
            query['location'] = {"$regex": location, "$options": "i"}
        if min_price is not None:
            query.setdefault('price', {})['$gte'] = min_price
        if max_price is not None:
            query.setdefault('price', {})['$lte'] = max_price
        if property_type:
            query['property_type'] = property_type
        if bedrooms is not None:
            query['bedrooms'] = bedrooms
            
        properties_list = []
        for prop in properties.find(query):
            # Keep the custom id field if it exists, otherwise use MongoDB _id
            if 'id' not in prop:
                prop['id'] = str(prop['_id'])
            del prop['_id']
            properties_list.append(prop)
            
        return properties_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Google Maps Static API endpoint
@app.get("/api/google-map")
async def get_google_map():
    """Get base64 encoded Google Maps static image"""
    try:
        # İstanbul coordinates for NiVALiS
        lat, lng = 41.0082, 28.9784
        zoom = 12
        size = "800x400"
        
        # Google Maps Static API URL
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyB3qFB2rvNb3cL9DLVlbvHiIwY42zekPpY')
        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size={size}&maptype=roadmap&markers=color:red%7Clabel:N%7C{lat},{lng}&key={api_key}"
        
        # Download the map image
        response = requests.get(map_url, timeout=10)
        
        if response.status_code == 200:
            # Convert to base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{image_base64}",
                "center": {"lat": lat, "lng": lng},
                "zoom": zoom
            }
        else:
            raise HTTPException(status_code=400, detail=f"Google Maps API error: {response.status_code}")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching map: {str(e)}")

# Initialize sample data
@app.on_event("startup")
async def initialize_data():
    try:
        # Add sample properties if none exist
        if properties.count_documents({}) == 0:
            sample_properties = [
                {
                    "id": str(uuid.uuid4()),
                    "title_tr": "Lüks Villa",
                    "title_en": "Luxury Villa",
                    "description_tr": "Modern tasarımı ve geniş bahçesi ile muhteşem villa",
                    "description_en": "Magnificent villa with modern design and large garden",
                    "price": 850000,
                    "location": "İstanbul, Beşiktaş",
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "size": 250.0,
                    "property_type": "Villa",
                    "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2MzR8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBob3VzZXxlbnwwfHx8fDE3NTMxODA2NTR8MA&ixlib=rb-4.1.0&q=85",
                    "featured": True,
                    "created_at": datetime.now()
                },
                {
                    "id": str(uuid.uuid4()),
                    "title_tr": "Modern Konut",
                    "title_en": "Modern Residence",
                    "description_tr": "Şehir merkezinde konforlu yaşam alanı",
                    "description_en": "Comfortable living space in the city center",
                    "price": 450000,
                    "location": "Ankara, Çankaya",
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "size": 180.0,
                    "property_type": "Apartment",
                    "image_url": "https://images.unsplash.com/photo-1706808849780-7a04fbac83ef?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwyfHxsdXh1cnklMjBob21lfGVufDB8fHx8MTc1MzE4MDY2MXww&ixlib=rb-4.1.0&q=85",
                    "featured": True,
                    "created_at": datetime.now()
                }
            ]
            properties.insert_many(sample_properties)
            
        # Add sample blog posts if none exist
        if blog_posts.count_documents({}) == 0:
            sample_posts = [
                {
                    "id": str(uuid.uuid4()),
                    "title_tr": "2024 Gayrimenkul Trendleri",
                    "title_en": "2024 Real Estate Trends",
                    "content_tr": "Bu yıl gayrimenkul sektöründe öne çıkan trendler...",
                    "content_en": "This year's prominent trends in the real estate sector...",
                    "created_at": datetime.now()
                },
                {
                    "id": str(uuid.uuid4()),
                    "title_tr": "Yatırım İpuçları",
                    "title_en": "Investment Tips",
                    "content_tr": "Gayrimenkul yatırımında dikkat edilmesi gerekenler...",
                    "content_en": "What to pay attention to in real estate investment...",
                    "created_at": datetime.now()
                }
            ]
            blog_posts.insert_many(sample_posts)
            
        print("Sample data initialized")
    except Exception as e:
        print(f"Error initializing data: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
