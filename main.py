from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import database
import models
import schemas
import crud
from auth import verify_password
from typing import List, Optional
import time
import secrets



# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Setup templates for frontend
templates = Jinja2Templates(directory="templates")

# For serving static files (CSS, JS later)
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== FRONTEND ROUTES ==========
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the app starts
    db = database.SessionLocal()
    try:
        # 1. Force create all tables (including the new ones)
        models.Base.metadata.create_all(bind=database.engine)
        
        # 2. Setup initial groups
        existing = db.query(models.GroupChat).first()
        if not existing:
            groups = [
                models.GroupChat(name="Python & Coding", description="Discussion for tech learners"),
                models.GroupChat(name="Language Exchange", description="Practice speaking different languages"),
                models.GroupChat(name="Music & Arts", description="Share your creative progress")
            ]
            db.add_all(groups)
            db.commit()
    except Exception as e:
        print(f"Error during startup: {e}")
    finally:
        db.close()
    
    yield
    # This runs when the app shuts down

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/dashboard-page")
def dashboard_page(request: Request, email: str):
    return templates.TemplateResponse("dashboard.html", {"request": request, "email": email})

@app.get("/api/bookings")
def get_bookings_api(email: str, db: Session = Depends(get_db)):
    return crud.get_user_bookings(db, email)

@app.get("/login-page")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register-page")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/profile-page")
def profile_page(request: Request, email: Optional[str] = None, view_email: Optional[str] = None):
    # Determine who we are looking at
    # If view_email is missing, we are looking at our own profile
    target = view_email if view_email else email
    
    # Crucial: Is the logged in user the same as the profile owner?
    is_owner = (email == target)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "email": email,         # The person logged in
        "view_email": target,   # The person being viewed
        "is_owner": is_owner    # Enables the "Edit" buttons
    })

@app.get("/matches-page")
def matches_page(request: Request, email: Optional[str] = None):
    if not email:
        return RedirectResponse("/login-page")
    return templates.TemplateResponse("matches.html", {"request": request, "email": email})

@app.get("/messages-page")
def messages_page(request: Request, email: Optional[str] = None):
    if not email:
        return RedirectResponse("/login-page")
    return templates.TemplateResponse("messages.html", {"request": request, "email": email})
# ========== FRONTEND ACTION ENDPOINTS ==========

@app.post("/register-user")
def register_user_frontend(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user exists
    db_user = crud.get_user_by_email(db, email=email)
    if db_user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Email already registered"
        })
    
    # Create user using existing API schema
    user_data = schemas.UserCreate(name=name, email=email, password=password)
    crud.create_user(db=db, user=user_data)
    
    # Redirect to profile
    return RedirectResponse(f"/profile-page?email={email}", status_code=303)

@app.post("/login-user")
def login_user_frontend(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "User not found"
        })
    
    is_valid = verify_password(password, user.password)
    if not is_valid:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid password"
        })
    
    # Login successful - redirect to profile
    return RedirectResponse(f"/profile-page?email={email}", status_code=303)

@app.post("/add-skill-frontend")
def add_skill_frontend(
    email: str = Form(...),
    skill_type: str = Form(...),
    skill_name: str = Form(...),
    skill_level: str = Form("intermediate"),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    if skill_type == "offer":
        skill_data = schemas.SkillOfferCreate(skill_name=skill_name, skill_level=skill_level)
        crud.add_skill_offer_by_email(db, email, skill_data)
    else:
        skill_request = schemas.SkillRequestCreate(skill_name=skill_name, description=description)
        crud.add_skill_request_by_email(db, email, skill_request)
    
    return RedirectResponse(f"/profile-page?email={email}", status_code=303)

@app.get("/video/check-incoming/{email}")
def check_incoming_call(email: str, db: Session = Depends(get_db)):
    call = crud.get_active_video_call(db, email)
    if call:
        return {
            "has_call": True,
            "room_id": call.room_id,
            "caller": call.user1_email
        }
    return {"has_call": False}

# ========== BACKEND APIs (UNCHANGED) ==========

@app.get("/")
def read_root():
    return {"message": "SkillSwap API - Now Email-Based!"}

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users", response_model=list[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

# NEW: Get user by email
@app.get("/users/{email}", response_model=schemas.UserWithSkillsResponse)
def get_user_by_email_endpoint(email: str, db: Session = Depends(get_db)):
    user = crud.get_user_skills_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# UPDATED: Skill endpoints using email
@app.post("/users/{email}/skills/offer")
def add_skill_offer(
    email: str, 
    skill: schemas.SkillOfferCreate, 
    db: Session = Depends(get_db)
):
    result = crud.add_skill_offer_by_email(db, email, skill)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Skill added successfully", "skill": result}

@app.post("/users/{email}/skills/request")
def add_skill_request(
    email: str,
    skill_request: schemas.SkillRequestCreate,
    db: Session = Depends(get_db)
):
    result = crud.add_skill_request_by_email(db, email, skill_request)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Skill request added successfully", "request": result}

@app.get("/skills/offers")
def get_all_skill_offers(db: Session = Depends(get_db)):
    return crud.get_skill_offers(db)

@app.get("/skills/requests")
def get_all_skill_requests(db: Session = Depends(get_db)):
    return crud.get_skill_requests(db)

# UPDATED: Matching endpoint using email
@app.get("/users/{email}/matches")
def get_user_matches(email: str, db: Session = Depends(get_db)):
    matches = crud.find_matches_by_email(db, email)
    user = crud.get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_email": email,
        "user_name": user.name,
        "matches_found": len(matches),
        "matches": matches
    }

# Password verification (keep this)
@app.post("/verify-password")
def verify_user_password(email: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_valid = verify_password(password, user.password)
    return {"password_correct": is_valid}

# NEW: Get user's own skills
@app.get("/users/{email}/profile")
def get_user_profile(email: str, db: Session = Depends(get_db)):
    user = crud.get_user_skills_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user.email,
        "name": user.name,
        "skills_offered": [
            {"skill_name": skill.skill_name, "level": skill.skill_level} 
            for skill in user.skills_offered
        ],
        "skills_needed": [
            {"skill_name": skill.skill_name, "description": skill.description} 
            for skill in user.skills_needed
        ]
    }

# Messaging Endpoints
@app.post("/messages/send")
def send_message_endpoint(
    sender_email: str,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db)
):
    result = crud.send_message(db, sender_email, message)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Message sent successfully", "message_id": result.id}

@app.get("/messages/{user_email}")
def get_messages_endpoint(
    user_email: str,
    db: Session = Depends(get_db)
):
    messages = crud.get_user_messages(db, user_email)
    return messages

@app.get("/messages/conversation/{user1_email}/{user2_email}")
def get_conversation_endpoint(
    user1_email: str,
    user2_email: str,
    db: Session = Depends(get_db)
):
    conversation = crud.get_conversation(db, user1_email, user2_email)
    return conversation

@app.post("/messages/mark-read/{user_email}/{other_user_email}")
def mark_messages_read_endpoint(
    user_email: str,
    other_user_email: str,
    db: Session = Depends(get_db)
):
    updated = crud.mark_messages_as_read(db, user_email, other_user_email)
    return {"updated_count": updated}

@app.get("/messages/unread/{user_email}")
def get_unread_count_endpoint(
    user_email: str,
    db: Session = Depends(get_db)
):
    count = crud.get_unread_count(db, user_email)
    return {"unread_count": count}


@app.post("/video/create", response_model=schemas.VideoSessionResponse)
def create_video_session_endpoint(
    session_data: schemas.VideoSessionCreate, # Changed to accept the Pydantic model
    db: Session = Depends(get_db)
):
    """Create a new video session room using JSON Body data"""
    # Pass the whole session_data object to crud
    session = crud.create_video_session(db, session_data)
    return session

@app.get("/video/sessions/{email}")
def get_user_video_sessions(email: str, db: Session = Depends(get_db)):
    """Get all video sessions for a user"""
    sessions = crud.get_video_sessions_by_user(db, email)
    return sessions

@app.post("/video/update-status/{room_id}")
def update_session_status(
    room_id: str,
    status: str = "active",  # "active" or "ended"
    db: Session = Depends(get_db)
):
    """Update video session status"""
    updated = crud.update_video_session_status(db, room_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Session status updated to {status}"}

@app.get("/video/room/{room_id}")
def get_video_room_info(room_id: str, db: Session = Depends(get_db)):
    """Get information about a video room"""
    session = db.query(models.VideoSession).filter(
        models.VideoSession.room_id == room_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "room_id": session.room_id,
        "user1_email": session.user1_email,
        "user2_email": session.user2_email,
        "meeting_url": session.meeting_url,
        "status": session.status,
        "created_at": session.created_at
    }
@app.post("/video/decline/{room_id}")
def decline_call_endpoint(room_id: str, db: Session = Depends(get_db)):
    crud.decline_video_call(db, room_id)
    return {"message": "Call declined"}

@app.post("/users/{email}/update")
def update_profile(email: str, name: str = Form(...), about: str = Form(None), 
                   linkedin: str = Form(None), github: str = Form(None), twitter: str = Form(None),
                   db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user: raise HTTPException(status_code=404)
    user.name = name
    user.about = about
    user.linkedin_url = linkedin
    user.github_url = github
    user.twitter_url = twitter
    db.commit()
    return RedirectResponse(f"/profile-page?email={email}", status_code=303)

# Profile Endpoint for View Only
@app.get("/profile/{view_email}")
def view_public_profile(request: Request, view_email: str, email: Optional[str] = None):
    """
    view_email: The person whose profile we want to see
    email: The logged-in user (from the query param)
    """
    is_owner = (view_email == email)
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "email": email,        # Logged-in user for the Navbar
        "view_email": view_email, # Profile being viewed
        "is_owner": is_owner   # Toggle for Edit buttons
    })

# --- FEED ROUTES ---


@app.get("/feed-page")
def feed_page(request: Request, email: str):
    return templates.TemplateResponse("feed.html", {"request": request, "email": email})

@app.get("/api/posts", response_model=List[schemas.PostResponse])
def get_all_posts(db: Session = Depends(get_db)):
    return crud.get_posts(db)

@app.post("/create-post")
def create_post_route(
    email: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db)
):
    post_data = schemas.PostCreate(content=content, category=category)
    crud.create_post(db, email, post_data)
    return RedirectResponse(f"/feed-page?email={email}", status_code=303)

# --- GROUP CHAT ROUTES ---

@app.get("/groups-page")
def groups_page(request: Request, email: str):
    return templates.TemplateResponse("groups.html", {"request": request, "email": email})

@app.get("/api/groups")
def get_groups(db: Session = Depends(get_db)):
    return crud.get_all_groups(db)

@app.get("/api/groups/{group_id}/messages")
def get_group_chat_messages(group_id: int, db: Session = Depends(get_db)):
    messages = crud.get_group_messages(db, group_id)
    # Ensure we return a list, even if it's empty
    return messages if messages else []

@app.post("/api/groups/{group_id}/send")
def send_group_message(
    group_id: int,
    email: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    crud.create_group_message(db, group_id, email, content)
    return {"status": "success"}

@app.post("/api/bookings/request")
def request_booking(
    learner_email: str = Form(...),
    teacher_email: str = Form(...),
    skill_name: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    db: Session = Depends(get_db)
):
    crud.create_booking(db, learner_email, teacher_email, skill_name, date, time)
    return RedirectResponse(f"/profile-page?email={learner_email}&view_email={teacher_email}&booked=true", status_code=303)

@app.post("/api/bookings/{booking_id}/update")
def update_booking_status(booking_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if booking:
        booking.status = status
        db.commit()
    return {"status": "updated"}