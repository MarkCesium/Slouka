from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo
from aiogram_dialog.widgets.text import Const
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.services.user import UserService

from .common import get_user
from .states import MainMenuSG, OnboardingSG


@inject
async def on_finish_onboarding(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if user:
        await user_service.complete_onboarding(user.id)

    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)  # pyright: ignore[reportUnknownMemberType]


onboarding_dialog = Dialog(
    Window(
        Const(
            "<b>Сардэчна запрашаем у Sloŭka!</b>\n\n"
            "Ваш асабісты трэнер па вывучэнні беларускай лексікі.\n\n"
            "Пашырайце свой слоўнікавы запас з дапамогай флэш-картак "
            "і практыкуйцеся з дапамогай паўтарэння з інтэрваламі."
        ),
        SwitchTo(Const("Далей →"), id="to_how", state=OnboardingSG.how_it_works),
        state=OnboardingSG.welcome,
    ),
    Window(
        Const(
            "<b>Як гэта працуе</b>\n\n"
            "1. <b>Пошук</b> — Увядзіце любое беларускае слова, каб знайсці яго\n"
            "2. <b>Захаваць</b> — Дадайце словы да сваіх калодак як флэш-карткі\n"
            "3. <b>Практыкаваць</b> — Практыка з прамежкавым паўтарэннем\n\n"
            "Сістэма плануе праверкі, каб вы бачылі словы "
            "акурат перад тым, як забудзеце іх."
        ),
        SwitchTo(Const("Далей →"), id="to_ready", state=OnboardingSG.ready),
        state=OnboardingSG.how_it_works,
    ),
    Window(
        Const("<b>Усё гатова!</b>\n\nДавайце пачнем з пошуку вашага першага слова."),
        Button(Const("Перайсці ў меню →"), id="finish", on_click=on_finish_onboarding),
        state=OnboardingSG.ready,
    ),
)
