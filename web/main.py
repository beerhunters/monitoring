import logging
from fastapi import FastAPI, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from models.models import User, Site, SystemSettings
from config import Config
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import urllib.parse
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
engine = create_async_engine(Config.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@app.on_event("startup")
async def startup_event():
    pass


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    raw_token = request.cookies.get("access_token")
    if not raw_token:
        return None
    try:
        raw_token = urllib.parse.unquote(raw_token)
        token = (
            raw_token[len("Bearer ") :]
            if raw_token.startswith("Bearer ")
            else raw_token
        )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except:
        return None


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=RedirectResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != Config.ADMIN_USERNAME or not pwd_context.verify(
        form_data.password, pwd_context.hash(Config.ADMIN_PASSWORD)
    ):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return response


@app.get("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(User))
        user_count = len(result.scalars().all())
        result = await session.execute(select(Site))
        site_count = len(result.scalars().all())
        result = await session.execute(
            select(SystemSettings).filter_by(key="check_interval")
        )
        settings = result.scalar_one_or_none()
        interval = settings.value if settings else Config.CHECK_INTERVAL
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user_count": user_count,
                "site_count": site_count,
                "check_interval": interval,
            },
        )


@app.get("/users", response_class=HTMLResponse)
async def users(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return templates.TemplateResponse(
            "users.html", {"request": request, "users": users}
        )


@app.get("/users/{user_id}/sites", response_class=HTMLResponse)
async def user_sites(
    request: Request, user_id: int, current_user: str = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(Site).filter_by(user_id=user_id))
        sites = result.scalars().all()
        return templates.TemplateResponse(
            "users.html", {"request": request, "sites": sites, "user_id": user_id}
        )


@app.post("/sites/{site_id}/delete", response_class=RedirectResponse)
async def delete_site(site_id: int, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(Site).filter_by(id=site_id))
        site = result.scalar_one_or_none()
        if site:
            await session.delete(site)
            await session.commit()
        return RedirectResponse(url="/users", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(
            select(SystemSettings).filter_by(key="check_interval")
        )
        settings = result.scalar_one_or_none()
        interval = settings.value if settings else Config.CHECK_INTERVAL
        return templates.TemplateResponse(
            "settings.html", {"request": request, "check_interval": interval}
        )


@app.post("/settings", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    check_interval: int = Form(...),
    current_user: str = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(
            select(SystemSettings).filter_by(key="check_interval")
        )
        settings = result.scalar_one_or_none()
        if settings:
            settings.value = str(check_interval)
        else:
            settings = SystemSettings(key="check_interval", value=str(check_interval))
            session.add(settings)
        await session.commit()
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "check_interval": check_interval,
                "success_message": "Интервал проверки успешно сохранён",
            },
        )


@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("broadcast.html", {"request": request})


@app.post("/broadcast", response_class=HTMLResponse)
async def send_broadcast(
    request: Request,
    message: str = Form(...),
    current_user: str = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        successful_count = 0
        failed_count = 0
        logger.info(f"Starting broadcast to {len(users)} users with message: {message}")
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        try:
            for user in users:
                try:
                    await bot.send_message(user.telegram_id, message)
                    successful_count += 1
                    logger.debug(f"Message sent to user {user.telegram_id}")
                except TelegramBadRequest as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to send message to user {user.telegram_id}: {str(e)}"
                    )
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Unexpected error sending message to user {user.telegram_id}: {str(e)}"
                    )
        finally:
            await bot.session.close()
        logger.info(
            f"Broadcast completed: {successful_count} successful, {failed_count} failed"
        )
        return templates.TemplateResponse(
            "broadcast.html",
            {
                "request": request,
                "successful_count": successful_count,
                "failed_count": failed_count,
                "broadcast_completed": True,
            },
        )


@app.get("/apple-touch-icon-precomposed.png")
@app.get("/apple-touch-icon.png")
@app.get("/favicon.ico")
async def apple_touch_icon():
    return FileResponse("web/static/favicon.ico")
