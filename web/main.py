from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from models.models import User, Site, SystemSettings, Base
from config import Config
from aiogram import Bot
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
import asyncio
import urllib.parse

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="web/templates")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"

engine = create_async_engine(Config.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Created JWT token: {encoded_jwt}")
    except Exception as e:
        logger.error(e)
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    if not token:
        raw_token = request.cookies.get("access_token")
        logger.info(f"Raw cookie value: {raw_token}")
        if raw_token:
            # Декодируем URL-кодированные символы, такие как %20
            raw_token = urllib.parse.unquote(raw_token)
            if raw_token.startswith("Bearer "):
                token = raw_token[len("Bearer ") :]
            else:
                token = raw_token
        logger.info(f"Extracted token from cookie: {token}")

    if not token:
        logger.warning("No token provided")
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("No username in token payload")
            return None
        return username
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        return None


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    logger.info("Rendering login page")
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=RedirectResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt with username: {form_data.username}")
    hashed_password = pwd_context.hash(Config.ADMIN_PASSWORD)
    if form_data.username == Config.ADMIN_USERNAME and pwd_context.verify(
        form_data.password, hashed_password
    ):
        access_token = create_access_token(data={"sub": form_data.username})
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,  # Для localhost
            samesite="lax",
            path="/",
            max_age=24 * 3600,
        )
        logger.info(f"Login successful, set cookie with token: Bearer {access_token}")
        return response
    logger.error("Invalid credentials")
    raise HTTPException(status_code=401, detail="Неверные учетные данные")


@app.get("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    logger.info("User logged out")
    return response


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        logger.warning("Unauthorized access to /, redirecting to /login")
        return RedirectResponse(url="/login", status_code=303)
    logger.info(f"Dashboard accessed by user: {current_user}")
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_alias(
    request: Request, current_user: str = Depends(get_current_user)
):
    if not current_user:
        logger.warning("Unauthorized access to /dashboard, redirecting to /login")
        return RedirectResponse(url="/login", status_code=303)
    logger.info(f"Dashboard accessed by user via /dashboard: {current_user}")
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/users", response_class=HTMLResponse)
async def users(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        logger.warning("Unauthorized access to /users, redirecting to /login")
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
        logger.warning(
            "Unauthorized access to /users/{user_id}/sites, redirecting to /login"
        )
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
        logger.warning(
            "Unauthorized access to /sites/{site_id}/delete, redirecting to /login"
        )
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(Site).filter_by(id=site_id))
        site = result.scalar_one_or_none()
        if site:
            await session.delete(site)
            await session.commit()
            logger.info(f"Site {site_id} deleted by user: {current_user}")
            return RedirectResponse(url=f"/users/{site.user_id}/sites", status_code=303)
        logger.error(f"Site {site_id} not found")
        raise HTTPException(status_code=404, detail="Сайт не найден")


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        logger.warning("Unauthorized access to /settings, redirecting to /login")
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


@app.post("/settings", response_class=RedirectResponse)
async def update_settings(
    check_interval: int = Form(...), current_user: str = Depends(get_current_user)
):
    if not current_user:
        logger.warning("Unauthorized access to /settings POST, redirecting to /login")
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
        logger.info(
            f"Settings updated by user: {current_user}, check_interval: {check_interval}"
        )
    return RedirectResponse(url="/settings", status_code=303)


@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        logger.warning("Unauthorized access to /broadcast, redirecting to /login")
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("broadcast.html", {"request": request})


@app.post("/broadcast", response_class=RedirectResponse)
async def send_broadcast(
    message: str = Form(...), current_user: str = Depends(get_current_user)
):
    if not current_user:
        logger.warning("Unauthorized access to /broadcast POST, redirecting to /login")
        return RedirectResponse(url="/login", status_code=303)
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        for user in users:
            try:
                await bot.send_message(user.telegram_id, message)
            except Exception as e:
                logger.error(
                    f"Failed to send broadcast to user {user.telegram_id}: {str(e)}"
                )
        await bot.session.close()
    logger.info(f"Broadcast sent by user: {current_user}")
    return RedirectResponse(url="/broadcast", status_code=303)


@app.get("/apple-touch-icon-precomposed.png")
@app.get("/apple-touch-icon.png")
@app.get("/favicon.ico")
async def apple_touch_icon():
    return Response(status_code=204)
