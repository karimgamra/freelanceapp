from fastapi import APIRouter ,Depends , HTTPException ,status, Query , Body
from psycopg2 import IntegrityError
from jose import JWTError, jwt
from sqlalchemy.orm import Session 
from ...models.user import User
from ...schemas.user import CreateUser, UserResponse ,UserLogin ,UpdateUser , UpdatePassword, AdminUserResponse
from ...db.dependencies.get_db import get_db
from ...core.hashing import hash_password , verify_password
from .auth import create_access_token , get_current_user , admin_require , create_refresh_token
import uuid
from app.utils.users import validate_uuid , ensure_not_admin , get_user_by_id  
from typing import Literal , Optional
import os
from dotenv import load_dotenv

router = APIRouter()


ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
SECRET_KEY = os.getenv("SECRET_KEY")


@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register (user :CreateUser ,db :Session = Depends (get_db)) :
    
    existing_user = db.query(User).filter(User.email == user.email.strip().lower()).first()
    if existing_user :
        raise HTTPException (status_code=409 , detail="user is already exit")
    
    try:
        new_user = User(
            name = user.name.strip(),
            email = user.email.strip().lower() ,
            password = hash_password(user.password) ,
            role = user.role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
    except IntegrityError :
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return new_user



@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login (user : UserLogin ,db :Session = Depends (get_db)) :
    
    existing_user = db.query(User).filter(User.email == user.email.strip().lower()).first()
    if not existing_user :
        raise HTTPException (status_code=404 , detail="user not found")
    
    if not verify_password (user.password , existing_user.password) :
        raise HTTPException (status_code=401 , detail="Password not correct")
    
    access_token = create_access_token({"email": existing_user.email, "id": str(existing_user.id), "role":existing_user.role})
    refresh_token = create_refresh_token({"email": existing_user.email, "id": str(existing_user.id), "role":existing_user.role})    
        
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/refresh-token")
def refresh_token (token : str = Body(...) , db:Session = Depends(get_db)) :
    try :
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        email = payload.get("email")
        role = payload.get("role")
    
        if not email or not role:
            raise HTTPException(status_code=404 , detail="invalid token")
        
        db_user = db.query(User).filter(User.email == email).first()
        if not db_user :
            raise HTTPException(status_code=404 , detail="User not found")    
        new_access_token = create_access_token({"email": email, "id": user_id, "role": role})
        return {"access_token": new_access_token}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

        


@router.get("/user")
def get_user (current_user :User = Depends (get_current_user)):
    return {"name" : current_user.name , "role": current_user.role , "email": current_user.email}


@router.get("/admin/user")
def get_all_user (
    user :UserResponse = Depends(admin_require) ,
    db : Session = Depends(get_db) ,
    limit : int = Query (5 ,ge=1, le=10),
    role :  Optional[Literal["client", "freelance"]] = None,
    is_banned : Optional[bool] = None,
    skip :int = Query(0, ge=0)
                  ):
    try: 
        
        query = db.query(User)
        
        if role is not None :
            query = query.filter(User.role == role)
        if is_banned is not None :
            query = query.filter(User.is_banned == is_banned)
        
        total = query.count()
        users = query.order_by(User.name).offset(skip).limit(limit).all()        
        return {
            "total" : total ,
            "limit" :limit ,
            "skip" : skip ,
            "users" :[db_user for db_user in users]
        }
    except Exception as e :
        raise HTTPException (
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching users"
        )

@router.put("/user")
def update_user(
    user: UpdateUser,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated= False
    if  user.email is not None:
        new_email = user.email.strip().lower()
        if new_email != current_user.email:
            existing_user = db.query(User).filter(User.email == new_email).first()
            if existing_user:
                raise HTTPException(status_code=409, detail="Email already in use")
            current_user.email = new_email
            updated = True

    
    if user.name is not None:
        current_user.name = user.name
        updated = True
    
    if user.password is not None:
        current_user.password = hash_password(user.password)
        updated = True
    
    if user.role is not None:
        current_user.role = user.role
        updated = True
        
    if updated :
        try :
            db.commit()
            db.refresh(current_user)
        except Exception as e :
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )

    return {"name" : current_user.name , "role": current_user.role , "email": current_user.email}



        
@router.put("/admin/user/{id}/ban")
def toggle_bon (id :str , user : User = Depends (admin_require) , db : Session = Depends(get_db)) :
    
    try :
        user_uuid = uuid.UUID(id)
    except ValueError :
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user :
            raise HTTPException(status_code=403 , detail="user not found")
    if target_user.role == "admin" :
        raise HTTPException(status_code=403, detail="Cannot ban another admin")

    
    try :
        target_user.is_banned = not target_user.is_banned
        db.commit()
        db.refresh(target_user)
        action = "banned" if target_user.is_banned else "unbanned"
        return {"detail": f"User {target_user.email} has been {action}."}

    except Exception as e :
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while ban the user"
        )


@router.delete("admin/user/{id}",status_code=status.HTTP_200_OK)
def delete_user_by_admin (id: str , user : User = Depends (admin_require) , db : Session = Depends(get_db)) :
           
    try :
        user_uuid = uuid.UUID(id)
    except ValueError :
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    
    user = db.query(User).filter(User.id == id).first()
    
    if not user :
            raise HTTPException(status_code=403 , detail="user not found")
    
    if user.role == "admin" :
        raise HTTPException(status_code=400, detail="Admin cannot delete themselves.")

    try :
        db.delete(user)
        db.commit()
        return {"detail": f"User with ID {id} deleted successfully"}

    except Exception as e :
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the user"
        )

    


@router.delete("/user")
def logout (db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) :
 
    
    user = db.query(User).filter(User.email == current_user.email).first()
    
    if not user :
        raise HTTPException (status_code=status.HTTP_404_NOT_FOUND , detail="User Not Found")
    try :
        db.delete(user)
        db.commit()
    except Exception as e :
        db.rollback()
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
    return {"detail" : "User deleted successfully"}

