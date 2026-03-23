from fastapi import APIRouter

router = APIRouter(tags=["search"])

@router.post("/")
def search():
    return {"results": []}

#dummy voor nu