from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import User, Site, SystemSettings
from bot.keyboard import get_main_keyboard
import validators

router = Router()


class AddSite(StatesGroup):
    url = State()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    username = message.from_user.username

    async with session as db:
        result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username)
            db.add(user)
            await db.commit()

        await message.answer(
            "Добро пожаловать в бот мониторинга сайтов!",
            reply_markup=get_main_keyboard(),
        )


@router.callback_query(F.data == "add_site")
async def add_site_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите URL сайта для мониторинга:")
    await state.set_state(AddSite.url)
    await callback.answer()


@router.message(AddSite.url)
async def process_url(message: Message, state: FSMContext, session: AsyncSession):
    url = message.text.strip()

    if not validators.url(url):
        await message.answer(
            "Некорректный URL. Введите валидный URL (например, https://example.com):"
        )
        return

    telegram_id = message.from_user.id

    async with session as db:
        result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()

        if user:
            result = await db.execute(select(Site).filter_by(user_id=user.id, url=url))
            if result.scalar_one_or_none():
                await message.answer("Этот URL уже отслеживается!")
            else:
                site = Site(url=url, user_id=user.id)
                db.add(site)
                await db.commit()
                await message.answer(
                    f"Добавлен {url} для мониторинга.", reply_markup=get_main_keyboard()
                )
        else:
            await message.answer(
                "Пользователь не найден. Используйте /start для регистрации."
            )

    await state.clear()


@router.callback_query(F.data == "my_sites")
async def my_sites_callback(callback: CallbackQuery, session: AsyncSession):
    telegram_id = callback.from_user.id

    async with session as db:
        result = await db.execute(
            select(Site).join(User).filter(User.telegram_id == telegram_id)
        )
        sites = result.scalars().all()

        if not sites:
            await callback.message.answer("Вы еще не добавили сайты.")
        else:
            response = "Ваши отслеживаемые сайты:\n"
            for site in sites:
                status = "✅ Доступен" if site.is_available else "❌ Недоступен"
                response += f"{site.url} - {status}\n/delete_{site.id} для удаления\n"
            await callback.message.answer(response, reply_markup=get_main_keyboard())

    await callback.answer()


@router.callback_query(F.data.startswith("delete_"))
async def delete_site_callback(callback: CallbackQuery, session: AsyncSession):
    site_id = int(callback.data.split("_")[1])

    async with session as db:
        result = await db.execute(select(Site).filter_by(id=site_id))
        site = result.scalar_one_or_none()

        if site:
            await db.delete(site)
            await db.commit()
            await callback.message.answer(
                f"Удален {site.url} из мониторинга.", reply_markup=get_main_keyboard()
            )
        else:
            await callback.message.answer("Сайт не найден.")

    await callback.answer()
