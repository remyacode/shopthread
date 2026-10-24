from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.security import hash_password, verify_password, create_access_token
from app.core.supabase import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    instagram_handle: str | None = None
    upi_id: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    vendor: dict

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest):
    # Check if email already exists
    existing = supabase.table("vendors").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create vendor
    vendor_data = {
        "email": body.email,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name,
        "instagram_handle": body.instagram_handle,
        "upi_id": body.upi_id
    }
    result = supabase.table("vendors").insert(vendor_data).execute()
    vendor = result.data[0]
    
    # Generate token
    token = create_access_token({"sub": vendor["id"]})
    
    # Remove password hash before returning
    vendor.pop("password_hash", None)
    
    return AuthResponse(access_token=token, vendor=vendor)

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    # Find vendor
    result = supabase.table("vendors").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    vendor = result.data[0]
    
    # Verify password
    if not verify_password(body.password, vendor["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_access_token({"sub": vendor["id"]})
    
    # Remove password hash before returning
    vendor.pop("password_hash", None)
    
    return AuthResponse(access_token=token, vendor=vendor)

@router.get("/me")
async def get_me(vendor: dict = __import__('fastapi').Depends(__import__('app.core.dependencies', fromlist=['get_current_vendor']).get_current_vendor)):
    vendor.pop("password_hash", None)
    return vendor
