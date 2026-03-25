from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.infra.tg.dialogs.states import MainMenuSG

router = Router(name="common")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Slouka — Belarusian Vocabulary Trainer</b>\n\n"
        "/start — Start the bot\n"
        "/help — Show this message\n"
        "/menu — Go to main menu\n",
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)
