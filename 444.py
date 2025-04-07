import aiohttp
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types import Message
from aiogram import F
from aiogram import Router

API_TOKEN = "7741280271:AAEUjYR_N9s-ouZ6LgnmCdfwB2pivfzVX-o"
YANDEX_WEATHER_API_KEY = ""
YANDEX_MAPS_API_KEY = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

user_context = {}

async def fetch_weather(city: str) -> str:
    url = f"https://api.weather.yandex.ru/v2/informers?lat=55.7558&lon=37.6173&apikey={YANDEX_WEATHER_API_KEY}"
    headers = {"X-Yandex-API-Key": YANDEX_WEATHER_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                temperature = data['fact']['temp']
                condition = data['fact']['condition']
                return f"Сегодня в городе {city} температура: {temperature}°C, условия: {condition}."
            else:
                return None

async def fetch_nearest_places(city: str, place_type: str) -> str:
    search_url = f"https://search-maps.yandex.ru/v1/?apikey={YANDEX_MAPS_API_KEY}&text={place_type}+в+городе+{city}&lang=ru_RU"

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status == 200:
                data = await response.json()
                if data['features']:
                    place = data['features'][0]['properties']['Name']
                    coordinates = data['features'][0]['geometry']['coordinates']
                    return f"Ближайший {place_type}: {place}, координаты: {coordinates[1]}, {coordinates[0]}"
                else:
                    return "Не удалось найти ближайшие места."
            else:
                return "Извините, сеть не ловит."

@router.message(F.command("start"))
async def start_command(message: Message):
    await message.answer("Здравствуйте! Как ваши дела?\nВыберите, что вы хотите:\n1. Про погоду\n2. Про локацию")

@router.message(F.text)
async def handle_choice(message: Message):
    chat_id = message.chat.id
    user_data = user_context.setdefault(chat_id, {})

    choice = message.text.strip()
    if choice == '1':
        await weather_command(message)
    elif choice == '2':
        await places_command(message)
    else:
        await message.answer("Пожалуйста, выберите 1 или 2.")

async def weather_command(message: Message):
    chat_id = message.chat.id
    user_context[chat_id].setdefault('awaiting_city', None)

    await message.answer("Назовите ваш город:")
    user_context[chat_id]['awaiting_city'] = 'weather'

@router.message(F.text)
async def handle_city_input(message: Message):
    chat_id = message.chat.id
    user_data = user_context.get(chat_id, {})

    if user_data.get('awaiting_city') == 'weather':
        city = message.text.strip()
        weather_info = await fetch_weather(city)

        if weather_info:
            await message.answer(f"Отлично, операция выполняется. {weather_info}")
        else:
            await message.answer("Не удалось получить информацию о погоде.")

        user_data.pop('awaiting_city', None)

    elif user_data.get('awaiting_city') == 'place_search':
        place_type = message.text.strip().lower()
        city = user_data.get('city')

        if city:
            places_info = await fetch_nearest_places(city, place_type)
            await message.answer(places_info)
        else:
            await message.answer("Назовите ваш город:")
            user_data['awaiting_city'] = 'place_search'

    else:
        user_data['city'] = message.text.strip()
        await message.answer("Город сохранен. Пожалуйста, введите тип места (ресторан, музей, спортзал):")
        user_data['awaiting_city'] = 'place_search'

@router.message(F.command("places"))
async def places_command(message: Message):
    chat_id = message.chat.id
    user_context.setdefault(chat_id, {})

    await message.answer("Назовите ваш город для поиска ближайших мест:")
    user_context[chat_id]['awaiting_city'] = 'place_search'


if __name__ == "__main__":
    dp.include_router(router)
    import asyncio

    asyncio.run(dp.start_polling(bot))
