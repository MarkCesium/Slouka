from aiogram.fsm.state import State, StatesGroup


class OnboardingSG(StatesGroup):
    welcome = State()
    how_it_works = State()
    ready = State()


class MainMenuSG(StatesGroup):
    menu = State()


class LookupSG(StatesGroup):
    enter_word = State()
    results = State()


class CardDisplaySG(StatesGroup):
    show = State()
    select_deck = State()
    create_deck = State()
    added = State()


class DeckManagementSG(StatesGroup):
    list_decks = State()
    create_deck = State()
    view_deck = State()


class ReviewSG(StatesGroup):
    select_deck = State()
    show_front = State()
    show_back = State()
    rate = State()
    session_complete = State()
