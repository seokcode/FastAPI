import sys
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, APIRouter, Request, Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .auth import get_current_user, verify_password, get_password_hash, logout

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not Found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str

@router.get("/edit-password", response_class=HTMLResponse)
async def edit_user_view(request: Request):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("edit-user-password.html", {"request": request, "user": user})


@router.post("/edit-password", response_class=HTMLResponse)
async def user_password_change(request: Request, password: str = Form(...),
                               new_password: str = Form(...), db: Session = Depends(get_db)):


    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_data = db.query(models.Users).filter(models.Users.username == user.get("username")).first()

    msg = "Incorrect Username or Password"

    if user_data is not None:
        if verify_password(password, user_data.hashed_password):
            user_data.hashed_password = get_password_hash(new_password)
            db.add(user_data)
            db.flush()
            db.commit()
            msg = "Password Updated Please Login Again"

            response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
            response.delete_cookie(key="access_token")
            return response

    return templates.TemplateResponse("edit-user-password.html", {"request": request, "msg": msg, "user": user})

