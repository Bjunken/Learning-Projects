from fastapi import FastAPI, Depends
from app.auth import verify_token

app = FastAPI()

@app.get("/public")
def public():
    return {"message": "Anyone can see this."}

@app.get("/protected")
def protected(user=Depends(verify_token)):
    return {
        "message": "protected data",
        "user": user["sub"],
        "role": user["role"]
    }