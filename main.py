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
from typing import Optional

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

@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login-page")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register-page")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/profile-page")
def profile_page(request: Request, email: Optional[str] = None):
    if not email:
        return RedirectResponse("/login-page")
    return templates.TemplateResponse("profile.html", {"request": request, "email": email})

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

# @app.get("/debug/user/{email}")
# def debug_user(email: str, db: Session = Depends(get_db)):
#     """Debug endpoint to see user data"""
#     user = crud.get_user_by_email(db, email)
#     if not user:
#         return {"error": "User not found"}
    
#     return {
#         "id": user.id,
#         "name": user.name,
#         "email": user.email,
#         "skills_offered_count": len(user.skills_offered),
#         "skills_needed_count": len(user.skills_needed)
#     }

# @app.get("/debug/messages/{email}")
# def debug_messages(email: str, db: Session = Depends(get_db)):
#     """Debug endpoint to see all messages for a user"""
#     messages = crud.get_user_messages(db, email)
#     result = []
#     for msg in messages:
#         result.append({
#             "id": msg.id,
#             "sender_id": msg.sender_id,
#             "sender_email": msg.sender.email if msg.sender else None,
#             "sender_name": msg.sender.name if msg.sender else None,
#             "receiver_id": msg.receiver_id,
#             "receiver_email": msg.receiver.email if msg.receiver else None,
#             "receiver_name": msg.receiver.name if msg.receiver else None,
#             "content": msg.content,
#             "timestamp": msg.timestamp,
#             "is_read": msg.is_read
#         })
#     return result