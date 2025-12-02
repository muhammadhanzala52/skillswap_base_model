from sqlalchemy.orm import Session
import models
import schemas
from auth import hash_password

# User operations
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_users(db: Session):
    return db.query(models.User).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# NEW: Get user ID from email (helper function)
def get_user_id_from_email(db: Session, email: str):
    user = get_user_by_email(db, email)
    return user.id if user else None

# Skill operations (UPDATED to use email)
def add_skill_offer_by_email(db: Session, email: str, skill: schemas.SkillOfferCreate):
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    new_skill = models.UserSkill(
        user_id=user.id,
        skill_name=skill.skill_name,
        skill_level=skill.skill_level
    )
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill

def add_skill_request_by_email(db: Session, email: str, skill_request: schemas.SkillRequestCreate):
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    new_request = models.SkillRequest(
        user_id=user.id,
        skill_name=skill_request.skill_name,
        description=skill_request.description
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

def get_skill_offers(db: Session):
    return db.query(models.UserSkill).all()

def get_skill_requests(db: Session):
    return db.query(models.SkillRequest).all()

# NEW: Get skills by email
def get_user_skills_by_email(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    return user

# UPDATED: Matching function to use email
def find_matches_by_email(db: Session, email: str):
    """Find users who need skills that this user offers"""
    user = get_user_by_email(db, email)
    if not user:
        return []
    
    matches = []
    
    # For each skill this user offers
    for offered_skill in user.skills_offered:
        # Find users who need this skill
        users_needing_skill = db.query(models.SkillRequest).filter(
            models.SkillRequest.skill_name == offered_skill.skill_name
        ).all()
        
        for request in users_needing_skill:
            if request.user_id != user.id:  # Don't match with self
                requester = get_user_by_id(db, request.user_id)
                matches.append({
                    "match_type": "you_can_teach",
                    "your_skill": offered_skill.skill_name,
                    "their_skill_level": offered_skill.skill_level,
                    "matched_user": {
                        "email": requester.email,
                        "name": requester.name
                    },
                    "their_request": request.description
                })
    
    # Also find users who can teach skills this user needs
    for needed_skill in user.skills_needed:
        # Find users who offer this skill
        users_offering_skill = db.query(models.UserSkill).filter(
            models.UserSkill.skill_name == needed_skill.skill_name
        ).all()
        
        for offer in users_offering_skill:
            if offer.user_id != user.id:  # Don't match with self
                offerer = get_user_by_id(db, offer.user_id)
                matches.append({
                    "match_type": "you_can_learn",
                    "skill_you_need": needed_skill.skill_name,
                    "their_skill_level": offer.skill_level,
                    "matched_user": {
                        "email": offerer.email,
                        "name": offerer.name
                    },
                    "their_offer": f"Can teach {offer.skill_name} at {offer.skill_level} level"
                })
    
    return matches


# Messaging Crud Operations
def send_message(db: Session, sender_email: str, message_data: schemas.MessageCreate):
    # Get sender and receiver
    sender = get_user_by_email(db, sender_email)
    receiver = get_user_by_email(db, message_data.receiver_email)
    
    if not sender or not receiver:
        return None
    
    # Create message
    new_message = models.Message(
        sender_id=sender.id,
        receiver_id=receiver.id,
        content=message_data.content
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

def get_user_messages(db: Session, user_email: str):
    user = get_user_by_email(db, user_email)
    if not user:
        return []
    
    # Get all messages where user is sender or receiver
    messages = db.query(models.Message).filter(
        (models.Message.sender_id == user.id) | 
        (models.Message.receiver_id == user.id)
    ).order_by(models.Message.timestamp.desc()).all()
    
    # Format response with user details
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_email": msg.sender.email if msg.sender else None,
            "sender_name": msg.sender.name if msg.sender else None,
            "receiver_id": msg.receiver_id,
            "receiver_email": msg.receiver.email if msg.receiver else None,
            "receiver_name": msg.receiver.name if msg.receiver else None,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "is_read": msg.is_read
        })
    
    return result

def get_conversation(db: Session, user1_email: str, user2_email: str):
    user1 = get_user_by_email(db, user1_email)
    user2 = get_user_by_email(db, user2_email)
    
    if not user1 or not user2:
        return []
    
    # Get messages between these two users
    messages = db.query(models.Message).filter(
        ((models.Message.sender_id == user1.id) & (models.Message.receiver_id == user2.id)) |
        ((models.Message.sender_id == user2.id) & (models.Message.receiver_id == user1.id))
    ).order_by(models.Message.timestamp.asc()).all()
    
    # Format response properly
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_email": msg.sender.email if msg.sender else None,
            "sender_name": msg.sender.name if msg.sender else "Unknown",
            "receiver_id": msg.receiver_id,
            "receiver_email": msg.receiver.email if msg.receiver else None,
            "receiver_name": msg.receiver.name if msg.receiver else "Unknown",
            "content": msg.content,
            "timestamp": msg.timestamp,
            "is_read": msg.is_read == 1
        })
    
    return result

def mark_messages_as_read(db: Session, user_email: str, other_user_email: str):
    user = get_user_by_email(db, user_email)
    other_user = get_user_by_email(db, other_user_email)
    
    if not user or not other_user:
        return 0
    
    # Mark messages from other_user to user as read
    updated = db.query(models.Message).filter(
        (models.Message.sender_id == other_user.id) &
        (models.Message.receiver_id == user.id) &
        (models.Message.is_read == 0)
    ).update({"is_read": 1})
    
    db.commit()
    return updated

def get_unread_count(db: Session, user_email: str):
    user = get_user_by_email(db, user_email)
    if not user:
        return 0
    
    count = db.query(models.Message).filter(
        (models.Message.receiver_id == user.id) &
        (models.Message.is_read == 0)
    ).count()
    
    return count