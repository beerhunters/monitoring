# # from sqlite3 import IntegrityError
# #
# # from aiogram import Router, F
# # from aiogram.types import Message, CallbackQuery
# # from aiogram.filters import CommandStart
# # from aiogram.fsm.context import FSMContext
# # from aiogram.fsm.state import State, StatesGroup
# # from sqlalchemy.ext.asyncio import AsyncSession
# # from sqlalchemy.future import select
# # from models.models import User, Site, SystemSettings
# # from bot.keyboard import get_main_keyboard
# # import validators
# # import logging
# #
# #
# # logger = logging.getLogger(__name__)
# #
# # router = Router()
# #
# #
# # class AddSite(StatesGroup):
# #     url = State()
# #
# #
# # @router.message(CommandStart())
# # async def start_command(message: Message, state: FSMContext, session: AsyncSession):
# #     telegram_id = message.from_user.id
# #     username = message.from_user.username
# #
# #     async with session as db:
# #         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
# #         user = result.scalar_one_or_none()
# #
# #         if not user:
# #             user = User(telegram_id=telegram_id, username=username)
# #             # db.add(user)
# #             # await db.commit()
# #             try:
# #                 db.add(user)
# #                 await db.commit()
# #             except IntegrityError:
# #                 await db.rollback()
# #
# #         await message.answer(
# #             "Добро пожаловать в бот мониторинга сайтов!",
# #             reply_markup=get_main_keyboard(),
# #         )
# #
# #
# # @router.callback_query(F.data == "add_site")
# # async def add_site_callback(callback: CallbackQuery, state: FSMContext):
# #     await callback.message.answer("Введите URL сайта для мониторинга:")
# #     await state.set_state(AddSite.url)
# #     await callback.answer()
# #
# #
# # @router.message(AddSite.url)
# # async def process_url(message: Message, state: FSMContext, session: AsyncSession):
# #     url = message.text.strip()
# #
# #     if not validators.url(url):
# #         await message.answer(
# #             "Некорректный URL. Введите валидный URL (например, https://example.com):"
# #         )
# #         return
# #
# #     telegram_id = message.from_user.id
# #
# #     async with session as db:
# #         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
# #         user = result.scalar_one_or_none()
# #
# #         if user:
# #             result = await db.execute(select(Site).filter_by(user_id=user.id, url=url))
# #             if result.scalar_one_or_none():
# #                 await message.answer("Этот URL уже отслеживается!")
# #             else:
# #                 site = Site(url=url, user_id=user.id)
# #                 db.add(site)
# #                 await db.commit()
# #                 await message.answer(
# #                     f"Добавлен {url} для мониторинга.", reply_markup=get_main_keyboard()
# #                 )
# #         else:
# #             await message.answer(
# #                 "Пользователь не найден. Используйте /start для регистрации."
# #             )
# #
# #     await state.clear()
# #
# #
# # @router.callback_query(F.data == "my_sites")
# # async def my_sites_callback(callback: CallbackQuery, session: AsyncSession):
# #     telegram_id = callback.from_user.id
# #
# #     async with session as db:
# #         result = await db.execute(
# #             select(Site).join(User).filter(User.telegram_id == telegram_id)
# #         )
# #         sites = result.scalars().all()
# #
# #         if not sites:
# #             await callback.message.answer("Вы еще не добавили сайты.")
# #         else:
# #             response = "Ваши отслеживаемые сайты:\n"
# #             for site in sites:
# #                 status = "✅ Доступен" if site.is_available else "❌ Недоступен"
# #                 response += f"{site.url} - {status}\n/delete_{site.id} для удаления\n"
# #             await callback.message.answer(response, reply_markup=get_main_keyboard())
# #
# #     await callback.answer()
# #
# #
# # @router.callback_query(F.data.startswith("delete_"))
# # async def delete_site_callback(callback: CallbackQuery, session: AsyncSession):
# #     site_id = int(callback.data.split("_")[1])
# #
# #     async with session as db:
# #         result = await db.execute(select(Site).filter_by(id=site_id))
# #         site = result.scalar_one_or_none()
# #
# #         if site:
# #             await db.delete(site)
# #             await db.commit()
# #             await callback.message.answer(
# #                 f"Удален {site.url} из мониторинга.", reply_markup=get_main_keyboard()
# #             )
# #         else:
# #             await callback.message.answer("Сайт не найден.")
# #
# #     await callback.answer()
# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery
# from aiogram.filters import Command
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from models.models import Site, User
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
#
# router = Router()
#
#
# class DeleteSiteState(StatesGroup):
#     waiting_for_url = State()
#
#
# def get_main_keyboard() -> InlineKeyboardMarkup:
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Добавить сайт", callback_data="add_site")],
#             [InlineKeyboardButton(text="Список сайтов", callback_data="list_sites")],
#         ]
#     )
#     return keyboard
#
#
# @router.message(Command("start"))
# async def start_command(message: Message, session: AsyncSession):
#     telegram_id = message.from_user.id
#     username = message.from_user.username or "unknown"
#
#     async with session as db:
#         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             user = User(telegram_id=telegram_id, username=username)
#             db.add(user)
#             await db.commit()
#
#     await message.answer(
#         "Добро пожаловать! Используйте /add <url> для добавления сайта, /delete <url> для удаления или /list для просмотра списка.",
#         reply_markup=get_main_keyboard(),
#     )
#
#
# @router.message(Command("add"))
# async def add_site_command(message: Message, session: AsyncSession):
#     args = message.text.split(maxsplit=1)
#     if len(args) < 2:
#         await message.answer(
#             "Пожалуйста, укажите URL сайта. Пример: /add https://example.com"
#         )
#         return
#
#     url = args[1]
#     telegram_id = message.from_user.id
#
#     async with session as db:
#         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             user = User(
#                 telegram_id=telegram_id,
#                 username=message.from_user.username or "unknown",
#             )
#             db.add(user)
#             await db.commit()
#
#         result = await db.execute(select(Site).filter_by(url=url, user_id=user.id))
#         site = result.scalar_one_or_none()
#         if site:
#             await message.answer(f"Сайт {url} уже добавлен.")
#         else:
#             site = Site(url=url, user_id=user.id, is_available=True)
#             db.add(site)
#             await db.commit()
#             await message.answer(
#                 f"Сайт {url} добавлен в мониторинг.", reply_markup=get_main_keyboard()
#             )
#
#
# @router.message(Command("list"))
# async def list_sites_command(message: Message, session: AsyncSession):
#     telegram_id = message.from_user.id
#
#     async with session as db:
#         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             await message.answer("Вы не зарегистрированы. Используйте /start.")
#             return
#
#         result = await db.execute(select(Site).filter_by(user_id=user.id))
#         sites = result.scalars().all()
#
#         if not sites:
#             await message.answer("У вас нет добавленных сайтов.")
#             return
#
#         response = "Ваши сайты:\n" + "\n".join(
#             f"{site.url} - {'Доступен' if site.is_available else 'Недоступен'} "
#             f"(Проверено: {site.last_checked.strftime('%Y-%m-%d %H:%M:%S MSK') if site.last_checked else 'Никогда'})"
#             for site in sites
#         )
#         await message.answer(response, reply_markup=get_main_keyboard())
#
#
# @router.message(Command("delete"))
# async def delete_site_command(
#     message: Message, session: AsyncSession, state: FSMContext
# ):
#     args = message.text.split(maxsplit=1)
#     if len(args) < 2:
#         await message.answer(
#             "Пожалуйста, укажите URL сайта. Пример: /delete https://example.com"
#         )
#         return
#
#     url = args[1]
#     telegram_id = message.from_user.id
#
#     async with session as db:
#         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             await message.answer("Вы не зарегистрированы. Используйте /start.")
#             return
#
#         result = await db.execute(select(Site).filter_by(url=url, user_id=user.id))
#         site = result.scalar_one_or_none()
#         if not site:
#             await message.answer(f"Сайт {url} не найден в вашем списке.")
#             return
#
#         # Сохраняем site_id и url в состоянии для последующей обработки
#         await state.update_data(site_id=site.id, url=site.url)
#         # Отправляем модальное окно для подтверждения
#         keyboard = InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [
#                     InlineKeyboardButton(
#                         text="Да, удалить", callback_data=f"confirm_delete_{site.id}"
#                     )
#                 ],
#                 [InlineKeyboardButton(text="Отмена", callback_data="cancel_delete")],
#             ]
#         )
#         await message.answer(
#             f"Вы уверены, что хотите удалить сайт {url}?", reply_markup=keyboard
#         )
#
#
# @router.callback_query(F.data.startswith("delete_"))
# async def delete_site_callback(callback: CallbackQuery, session: AsyncSession):
#     site_id = int(callback.data.split("_")[1])
#
#     async with session as db:
#         result = await db.execute(select(Site).filter_by(id=site_id))
#         site = result.scalar_one_or_none()
#
#         if site:
#             # Отправляем модальное окно для подтверждения
#             keyboard = InlineKeyboardMarkup(
#                 inline_keyboard=[
#                     [
#                         InlineKeyboardButton(
#                             text="Да, удалить",
#                             callback_data=f"confirm_delete_{site.id}",
#                         )
#                     ],
#                     [
#                         InlineKeyboardButton(
#                             text="Отмена", callback_data="cancel_delete"
#                         )
#                     ],
#                 ]
#             )
#             await callback.message.answer(
#                 f"Вы уверены, что хотите удалить сайт {site.url}?",
#                 reply_markup=keyboard,
#             )
#         else:
#             await callback.message.answer(
#                 "Сайт не найден.", reply_markup=get_main_keyboard()
#             )
#
#     await callback.answer()
#
#
# @router.callback_query(F.data.startswith("confirm_delete_"))
# async def confirm_delete_site_callback(callback: CallbackQuery, session: AsyncSession):
#     site_id = int(callback.data.split("_")[2])
#
#     async with session as db:
#         result = await db.execute(select(Site).filter_by(id=site_id))
#         site = result.scalar_one_or_none()
#
#         if site:
#             url = site.url
#             await db.delete(site)
#             await db.commit()
#             await callback.message.answer(
#                 f"Сайт {url} удален из мониторинга.", reply_markup=get_main_keyboard()
#             )
#         else:
#             await callback.message.answer(
#                 "Сайт не найден.", reply_markup=get_main_keyboard()
#             )
#
#     await callback.answer()
#
#
# @router.callback_query(F.data == "cancel_delete")
# async def cancel_delete_callback(callback: CallbackQuery):
#     await callback.message.answer(
#         "Удаление отменено.", reply_markup=get_main_keyboard()
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "add_site")
# async def add_site_callback(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Введите URL сайта для добавления:")
#     await state.set_state(DeleteSiteState.waiting_for_url)
#     await callback.answer()
#
#
# @router.message(DeleteSiteState.waiting_for_url)
# async def process_add_site_url(
#     message: Message, session: AsyncSession, state: FSMContext
# ):
#     url = message.text.strip()
#     telegram_id = message.from_user.id
#
#     async with session as db:
#         result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             user = User(
#                 telegram_id=telegram_id,
#                 username=message.from_user.username or "unknown",
#             )
#             db.add(user)
#             await db.commit()
#
#         result = await db.execute(select(Site).filter_by(url=url, user_id=user.id))
#         site = result.scalar_one_or_none()
#         if site:
#             await message.answer(
#                 f"Сайт {url} уже добавлен.", reply_markup=get_main_keyboard()
#             )
#         else:
#             site = Site(url=url, user_id=user.id, is_available=True)
#             db.add(site)
#             await db.commit()
#             await message.answer(
#                 f"Сайт {url} добавлен в мониторинг.", reply_markup=get_main_keyboard()
#             )
#
#     await state.clear()
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.models import User, Site
import validators
import logging

logger = logging.getLogger(__name__)

router = Router()


class AddSiteState(StatesGroup):
    url = State()


def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить сайт", callback_data="add_site")],
            [InlineKeyboardButton(text="Список сайтов", callback_data="my_sites")],
        ]
    )
    return keyboard


@router.message(CommandStart())
async def start_command(message: Message, session: AsyncSession):
    telegram_id = message.from_user.id
    username = message.from_user.username or "unknown"

    async with session as db:
        result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username)
            try:
                db.add(user)
                await db.commit()
            except IntegrityError:
                await db.rollback()
                logger.warning(
                    f"Failed to add user {telegram_id} due to IntegrityError, user likely exists"
                )

    await message.answer(
        "Добро пожаловать в бот мониторинга сайтов! Используйте /add <url> для добавления сайта, /delete <url> для удаления или /list для просмотра списка.",
        reply_markup=get_main_keyboard(),
    )


@router.message(Command("add"))
async def add_site_command(message: Message, session: AsyncSession):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите URL сайта. Пример: /add https://example.com"
        )
        return

    url = args[1].strip()
    if not validators.url(url):
        await message.answer(
            "Некорректный URL. Введите валидный URL (например, https://example.com)"
        )
        return

    telegram_id = message.from_user.id

    async with session as db:
        result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=message.from_user.username or "unknown",
            )
            try:
                db.add(user)
                await db.commit()
            except IntegrityError:
                await db.rollback()
                logger.warning(
                    f"Failed to add user {telegram_id} due to IntegrityError"
                )

        result = await db.execute(select(Site).filter_by(url=url, user_id=user.id))
        site = result.scalar_one_or_none()
        if site:
            await message.answer(
                f"Сайт {url} уже добавлен.", reply_markup=get_main_keyboard()
            )
        else:
            site = Site(url=url, user_id=user.id, is_available=True)
            db.add(site)
            await db.commit()
            await message.answer(
                f"Сайт {url} добавлен в мониторинг.", reply_markup=get_main_keyboard()
            )


@router.message(Command("list"))
async def list_sites_command(message: Message, session: AsyncSession):
    telegram_id = message.from_user.id

    async with session as db:
        result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(
                "Вы не зарегистрированы. Используйте /start.",
                reply_markup=get_main_keyboard(),
            )
            return

        result = await db.execute(select(Site).filter_by(user_id=user.id))
        sites = result.scalars().all()

        if not sites:
            await message.answer(
                "У вас нет добавленных сайтов.", reply_markup=get_main_keyboard()
            )
            return

        response = "Ваши отслеживаемые сайты:\n"
        for site in sites:
            status = "✅ Доступен" if site.is_available else "❌ Недоступен"
            response += (
                f"{site.url} - {status} "
                f"(Проверено: {site.last_checked.strftime('%Y-%m-%d %H:%M:%S MSK') if site.last_checked else 'Никогда'})\n"
                f"/delete_{site.id} для удаления\n"
            )
        await message.answer(response, reply_markup=get_main_keyboard())


@router.message(Command("delete"))
async def delete_site_command(
    message: Message, session: AsyncSession, state: FSMContext
):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите URL сайта или ID. Пример: /delete https://example.com или /delete 123"
        )
        return

    input_data = args[1].strip()
    telegram_id = message.from_user.id

    async with session as db:
        result = await db.execute(select(User).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(
                "Вы не зарегистрированы. Используйте /start.",
                reply_markup=get_main_keyboard(),
            )
            return

        site = None
        if input_data.isdigit():  # Проверяем, является ли ввод ID
            site_id = int(input_data)
            result = await db.execute(
                select(Site).filter_by(id=site_id, user_id=user.id)
            )
            site = result.scalar_one_or_none()
        else:  # Считаем, что это URL
            if not validators.url(input_data):
                await message.answer(
                    "Некорректный URL. Введите валидный URL (например, https://example.com) или ID сайта."
                )
                return
            result = await db.execute(
                select(Site).filter_by(url=input_data, user_id=user.id)
            )
            site = result.scalar_one_or_none()

        if not site:
            await message.answer(
                f"Сайт {input_data} не найден в вашем списке.",
                reply_markup=get_main_keyboard(),
            )
            return

        # Сохраняем site_id и url в состоянии для последующей обработки
        await state.update_data(site_id=site.id, url=site.url)
        # Отправляем модальное окно для подтверждения
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Да, удалить", callback_data=f"confirm_delete_{site.id}"
                    )
                ],
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_delete")],
            ]
        )
        await message.answer(
            f"Вы уверены, что хотите удалить сайт {site.url}?", reply_markup=keyboard
        )


@router.callback_query(F.data == "add_site")
async def add_site_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите URL сайта для добавления:")
    await state.set_state(AddSiteState.url)
    await callback.answer()


@router.message(AddSiteState.url)
async def process_add_site_url(
    message: Message, session: AsyncSession, state: FSMContext
):
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
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=message.from_user.username or "unknown",
            )
            try:
                db.add(user)
                await db.commit()
            except IntegrityError:
                await db.rollback()
                logger.warning(
                    f"Failed to add user {telegram_id} due to IntegrityError"
                )

        result = await db.execute(select(Site).filter_by(url=url, user_id=user.id))
        site = result.scalar_one_or_none()
        if site:
            await message.answer(
                f"Сайт {url} уже добавлен.", reply_markup=get_main_keyboard()
            )
        else:
            site = Site(url=url, user_id=user.id, is_available=True)
            db.add(site)
            await db.commit()
            await message.answer(
                f"Сайт {url} добавлен в мониторинг.", reply_markup=get_main_keyboard()
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
            await callback.message.answer(
                "Вы еще не добавили сайты.", reply_markup=get_main_keyboard()
            )
        else:
            response = "Ваши отслеживаемые сайты:\n"
            for site in sites:
                status = "✅ Доступен" if site.is_available else "❌ Недоступен"
                response += (
                    f"{site.url} - {status} "
                    f"(Проверено: {site.last_checked.strftime('%Y-%m-%d %H:%M:%S MSK') if site.last_checked else 'Никогда'})\n"
                    f"/delete {site.id} для удаления\n"
                )
            await callback.message.answer(response, reply_markup=get_main_keyboard())

    await callback.answer()


@router.callback_query(F.data.startswith("delete_"))
async def delete_site_callback(callback: CallbackQuery, session: AsyncSession):
    site_id = int(callback.data.split("_")[1])

    async with session as db:
        result = await db.execute(select(Site).filter_by(id=site_id))
        site = result.scalar_one_or_none()

        if site:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Да, удалить",
                            callback_data=f"confirm_delete_{site.id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Отмена", callback_data="cancel_delete"
                        )
                    ],
                ]
            )
            await callback.message.answer(
                f"Вы уверены, что хотите удалить сайт {site.url}?",
                reply_markup=keyboard,
            )
        else:
            await callback.message.answer(
                "Сайт не найден.", reply_markup=get_main_keyboard()
            )

    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_site_callback(callback: CallbackQuery, session: AsyncSession):
    site_id = int(callback.data.split("_")[2])

    async with session as db:
        result = await db.execute(select(Site).filter_by(id=site_id))
        site = result.scalar_one_or_none()

        if site:
            url = site.url
            await db.delete(site)
            await db.commit()
            await callback.message.answer(
                f"Сайт {url} удален из мониторинга.", reply_markup=get_main_keyboard()
            )
        else:
            await callback.message.answer(
                "Сайт не найден.", reply_markup=get_main_keyboard()
            )

    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_callback(callback: CallbackQuery):
    await callback.message.answer(
        "Удаление отменено.", reply_markup=get_main_keyboard()
    )
    await callback.answer()
