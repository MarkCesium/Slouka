"""All user-facing text strings for the Slouka bot, organized by namespace."""


class Buttons:
    """Shared button labels used across multiple dialogs."""

    BACK = "← Назад"
    MENU = "← Меню"
    CREATE_DECK = "➕ Стварыць калодку"
    CONFIRM_DELETE = "🗑 Так, выдаліць"
    CANCEL_DELETE = "← Не, назад"


class Common:
    """Shared messages used across multiple dialogs."""

    ENTER_DECK_NAME = "Калі ласка, увядзіце назву калодкі."
    NO_DECKS = "\nЯшчэ няма калодак. Стварыце новую!"
    CREATE_DECK_TITLE = "<b>Стварыць новую калодку</b>\n\nУвядзіце назву калодкі:"


class MainMenu:
    TITLE = "<b>Галоўнае меню</b>\n\nШто б вы хацелі зрабіць?"
    STREAK = "\n🔥 Серыя: {streak} дз."
    SEARCH = "🔍 Пошук слова"
    DECKS = "📚 Мае калодкі"
    PRACTICE = "🧠 Практыка"
    SETTINGS = "⚙️ Налады"


class Onboarding:
    WELCOME = (
        "<b>Сардэчна запрашаем у Sloŭka!</b>\n\n"
        "Ваш асабісты трэнер па вывучэнні беларускай лексікі.\n\n"
        "Пашырайце свой слоўнікавы запас з дапамогай флэш-картак "
        "і практыкуйцеся з дапамогай паўтарэння з інтэрваламі."
    )
    HOW_IT_WORKS = (
        "<b>Як гэта працуе</b>\n\n"
        "1. <b>Пошук</b> — Увядзіце любое беларускае слова, каб знайсці яго\n"
        "2. <b>Захаваць</b> — Дадайце словы да сваіх калодак як флэш-карткі\n"
        "3. <b>Практыкаваць</b> — Практыка з прамежкавым паўтарэннем\n\n"
        "Сістэма плануе праверкі, каб вы бачылі словы "
        "акурат перад тым, як забудзеце іх."
    )
    READY = "<b>Усё гатова!</b>\n\nДавайце пачнем з пошуку вашага першага слова."
    NEXT = "Далей →"
    GO_TO_MENU = "Перайсці ў меню →"


class Lookup:
    TITLE = "<b>Пошук слова</b>\n\nУвядзіце слова для пошуку (беларускае ці рускае):"
    ENTER_WORD = "Калі ласка, увядзіце слова."
    NO_RESULTS_FOR = "Не знойдзена вынікаў для <b>{word}</b>. Паспрабуйце іншае слова."
    NO_RESULTS = "Не знойдзена вынікаў."
    PREV = "← Папярэдні"
    NEXT = "Наступны →"
    ADD_TO_DECK = "📥 Дадаць да калодкі"
    NEW_SEARCH = "🔍 Новы пошук"


class CardDisplay:
    SELECT_DECK = "<b>Абярыце калодку:</b>"
    CARD_DATA_ERROR = "Памылка: няма даных карткі."
    WORD_ALREADY_IN_DECK = "Гэтае слова ўжо ёсць у гэтай калодке!"
    CARD_ADDED = "Картка <b>{word}</b> дададзена да калодкі!"
    BACK_TO_RESULTS = "← Назад да вынікаў"


class DeckManagement:
    MY_DECKS = "<b>Мае калодкі</b>\n"
    DECK_INFO = (
        "<b>{deck_name}</b>\n\n"
        "Агульная колькасць картак: {total}\n"
        "Новыя карткі: {new}\n"
        "Да практыкі: {due}"
    )
    RENAME_TITLE = (
        "<b>Змяніць назву калодкі</b>\n\nБягучая назва: {deck_name}\nУвядзіце новую назву:"
    )
    ENTER_NEW_NAME = "Калі ласка, увядзіце новую назву калодкі."
    CONFIRM_DELETE_DECK = (
        '<b>Выдаліць калодку "{deck_name}"?</b>\n\n'
        "Усе карткі ({total}) будуць выдалены.\n"
        "Гэта дзеянне нельга адмяніць."
    )
    CARDS_IN_DECK = "<b>Карткі ў калодцы «{deck_name}»</b>\n\n{cards_text}"
    NO_CARDS = "\nУ гэтай калодцы яшчэ няма картак."
    CARD_DETAIL = "<b>{word}</b>\n\n{definition}{examples}"
    CONFIRM_DELETE_CARD = '<b>Выдаліць картку "{word}"?</b>\n\nГэта дзеянне нельга адмяніць.'
    PROGRESS_RESET = "Прагрэс скінуты"
    START_REVIEW = "🧠 Пачаць практыку"
    VIEW_CARDS = "📋 Карткі"
    RENAME = "📝 Змяніць назву"
    DELETE_DECK = "🗑 Выдаліць калодку"
    RESET_PROGRESS = "🔄 Скінуць прагрэс"
    DELETE_CARD = "🗑 Выдаліць картку"
    PREV_PAGE = "‹"
    NEXT_PAGE = "›"


class Review:
    SELECT_DECK = "<b>Абярыце калодку для практыкі:</b>"
    NO_DECKS = "\nНяма калодак з карткамі для практыкі."
    NO_CARDS = "Няма картак для практыкі ў гэтай калодцы."
    NO_PRACTICE_CARDS = "Няма картак для практыкі."
    SHOW_ANSWER = "Паказаць адказ"
    RATE_PROMPT = "\n\nЯк добра вы ведаеце гэтае слова?"
    AGAIN = "Дрэнна"
    HARD = "Цяжка"
    GOOD = "Нармалёва"
    EASY = "Лёгка"
    SESSION_COMPLETE = "<b>Практыка завершана!</b>\n\nВы праглядзелі {reviewed} картку(і)."


class Settings:
    TITLE = (
        "<b>⚙️ Налады</b>\n\nАпавяшчэнні: {status}\nЧас: {hour}:{minute}\nЧасавы пояс: {timezone}"
    )
    ENABLED = "✅ Уключаны"
    DISABLED = "❌ Выключаны"
    TOGGLE_DISABLE = "Выключыць апавяшчэнні"
    TOGGLE_ENABLE = "Уключыць апавяшчэнні"
    CHANGE_TIME = "🕐 Змяніць час"
    CHANGE_TIMEZONE = "🌍 Змяніць часавы пояс"
    SELECT_HOUR = "<b>Абярыце гадзіну апавяшчэння:</b>"
    SELECT_MINUTE = "<b>Абярыце хвіліны ({selected_hour}:??):</b>"
    TZ_METHOD = "<b>Як вызначыць часавы пояс?</b>"
    TZ_SEND_LOCATION = "📍 Адправіць месцазнаходжанне"
    TZ_SEARCH_BY_CITY = "🔍 Пошук па горадзе"
    TZ_ENTER_CITY = "<b>Увядзіце назву горада</b> (напрыклад, Minsk, Warsaw, Tokyo):"
    TZ_SELECT = "<b>Абярыце часавы пояс:</b>"
    TZ_SEARCH_AGAIN = "🔍 Шукаць яшчэ"
    TZ_CONFIRM = "<b>Ваш часавы пояс:</b> {selected_tz_label}\n\nПацвердзіць?"
    TZ_CONFIRM_BTN = "✅ Пацвердзіць"
    TZ_CLICK_BUTTON = "Націсніце кнопку ніжэй, каб адправіць месцазнаходжанне:"
    TZ_DETECT_FAILED = "Не ўдалося вызначыць часавы пояс. Паспрабуйце пошук па горадзе."
    TZ_LOCATION_RECEIVED = "📍 Месцазнаходжанне атрымана!"
    TZ_SEARCH_NO_RESULTS = "Нічога не знойдзена. Паспрабуйце яшчэ раз."


class Notifications:
    TEXT = "Вітаю, <b>{name}</b>! 👋\n\nУ цябе ёсць карткі для паўтарэння. Час трэніравацца! 📚"
