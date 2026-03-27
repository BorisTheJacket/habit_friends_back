from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
from typing import Optional
import os

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # Actually, for RS256, we need public key

# For Supabase, JWT is RS256, so we need to fetch the public key from jwks
def get_supabase_public_key():
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="SUPABASE_URL not set")
    jwks_url = f"{SUPABASE_URL}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
    jwks = response.json()
    # Assuming the first key is the one
    key = jwks['keys'][0]
    # For RS256, need to construct the public key
    from cryptography.hazmat.primitives import serialization
    import base64
    n = base64.urlsafe_b64decode(key['n'] + '==')
    e = base64.urlsafe_b64decode(key['e'] + '==')
    from cryptography.hazmat.primitives.asymmetric import rsa
    public_numbers = rsa.RSAPublicNumbers(e=int.from_bytes(e, 'big'), n=int.from_bytes(n, 'big'))
    public_key = public_numbers.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode()

public_key = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    global public_key
    if public_key is None:
        public_key = get_supabase_public_key()
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="authenticated")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")