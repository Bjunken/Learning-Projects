from fastapi import Depends, HTTPException
from jose import jwt
from app.auth import SECRET_KEY, ALGORITHM, ROLE_HIERARCHY

def required_min_role(required_role: str):
    def checker(token: str):
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")


        if ROLE_HIERARCHY[user_role] < ROLE_HIERARCHY[required_role]:
            raise HTTPException(403, "Not enough permissions")
    return checker

@app.get("/admin")
def admin_only(dep=Depends(required_min_role("admin"))):
    return {"message": "Admin access"}

@app.get("/moderator")
def mod_only(dep=Depends(required_min_role("moderator"))):
    return {"message": "Moderator access"}
