from fastapi import APIRouter

router = APIRouter(tags=["auth"])

@router.post("/login")
def login():
    # dummy shit kunne we later nog veranderen 
    return {"message": "todo"}
