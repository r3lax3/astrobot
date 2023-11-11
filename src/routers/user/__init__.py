from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    User
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from src import config
from src.scheduler import EveryDayPredictionScheduler
from src.routers import messages
from src.routers.states import ProfileSettings, MainMenu, Subscription
from src.routers.user.birth import r as birth_router
from src.routers.user.technical_support import r as technical_support_router
from src.routers.user.prediction import r as prediction_router
from src.routers.user.subsription import r as subsription_router
from src.routers.user.card_of_day import r as card_of_day_router
from src.routers.user.compatibility import r as compatibility_router
from src.routers.user.profile_settings import r as profile_settings_router
from src.routers.user.general_predictions import r as general_predictions_router
from src.routers.user.moon_in_sign import r as moon_in_sign_router

from src.database import Database
from src.database.models import Location, User as DBUser

from src.keyboard_manager import KeyboardManager, bt
from src.utils import get_location_by_coords, get_timezone_offset


r = Router()
r.include_routers(
    birth_router,
    profile_settings_router,
    technical_support_router,
    prediction_router,
    subsription_router,
    compatibility_router,
    general_predictions_router,
    card_of_day_router,
    moon_in_sign_router
)

start_video: str = config.get(
    'files.start_video'
)
database_datetime_format: str = config.get(
    'database.datetime_format'
)
not_implemented_list = [
    bt.dreams, 
    bt.theme
]
subscription_test_period_in_days: int = config.get(
    'subscription.test_period_in_days'
)


@r.message(F.text, F.text == '/test')
async def test_func(
    message: Message,
    database: Database
):
    message_ids = [2190, 2191, 2192, 2193, 2194, 2195, 2196, 2197, 2198, 2199, 2200, 2201, 2202, 2203, 2204, 2205, 2206, 2207, 2208, 2209, 2210, 2211, 2212, 2213, 2214, 2215, 2216, 2217, 2218, 2219, 2220, 2221, 2222, 2223, 2224, 2225, 2226, 2227, 2228, 2229, 2230, 2231, 2232, 2233, 2234, 2235, 2236, 2237, 2238, 2239, 2240, 2241, 2242, 2243, 2244, 2245, 2246, 2247, 2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257, 2258, 2259, 2260, 2261, 2262, 2263, 2264, 2265, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2274, 2275, 2276, 2277, 2278, 2279, 2280, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288, 2289, 2290, 2291, 2292, 2293, 2294, 2295, 2296, 2297, 2298, 2299, 2300, 2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309, 2310, 2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320, 2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334, 2335, 2336, 2337, 2338, 2339, 2340, 2341, 2342, 2343, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2351, 2352, 2353, 2354, 2355, 2356, 2357, 2358, 2359, 2360, 2361, 2362, 2363, 2364, 2365, 2366, 2367, 2368, 2369, 2370, 2371, 2372, 2373, 2374, 2375, 2376, 2377, 2378, 2379, 2380, 2381, 2382, 2383, 2384, 2385, 2386, 2387, 2388, 2389, 2390, 2391, 2392, 2393, 2394, 2395, 2396, 2397, 2398, 2399, 2400, 2401, 2402, 2403, 2404, 2405, 2406, 2407, 2408, 2409, 2410, 2411, 2412, 2413, 2414, 2415, 2416, 2417, 2418, 2419, 2420, 2421, 2422, 2423, 2424, 2425, 2426, 2427, 2428, 2429, 2430, 2431, 2432, 2433, 2434, 2435, 2436, 2437, 2438, 2439, 2440, 2441, 2442, 2443, 2444, 2445, 2446, 2447, 2448, 2449, 2450, 2451, 2452, 2453, 2454, 2455, 2456, 2457, 2458, 2459, 2460, 2461, 2462, 2463, 2464, 2465, 2466, 2467, 2468, 2469, 2470, 2471, 2472, 2473, 2474, 2475, 2476, 2477, 2478, 2479, 2480, 2481, 2482, 2483, 2484, 2485, 2486, 2487, 2488, 2489, 2490, 2491, 2492, 2493, 2494, 2495, 2496, 2497, 2498, 2499, 2500, 2501, 2502, 2503, 2504, 2505, 2506, 2507, 2508, 2509, 2510, 2511, 2512, 2513, 2514, 2515, 2516, 2517, 2518, 2519, 2520, 2521, 2522, 2523, 2524, 2525, 2526, 2527, 2528, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 2538, 2539, 2540, 2541, 2542, 2543, 2544, 2545, 2546, 2547, 2548, 2549, 2550, 2551, 2552, 2553, 2554, 2555, 2556, 2557, 2558, 2559, 2560, 2561, 2562, 2563, 2564, 2565, 2566, 2567, 2568, 2569, 2570, 2571, 2572, 2573, 2574, 2575, 2576, 2577, 2578, 2579, 2580, 2581, 2582, 2583, 2584, 2585, 2586, 2587, 2588, 2589, 2590, 2591, 2592, 2593, 2594, 2595, 2596, 2597, 2598, 2599, 2600, 2601, 2602, 2603, 2604, 2605, 2606]
    for message_id in message_ids:
        database.add_card_of_day(
            message_id=message_id
        )


@r.callback_query(
    F.data == 'Попробовать зайти ещё раз'
)
async def try_start_again_for_sub(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await user_command_start_handler(
        callback.message,
        state, 
        keyboards
    )



@r.message(CommandStart())
async def user_command_start_handler(
    message: Message,
    state: FSMContext,
    bot: Bot
    # database: Database,
    # event_from_user: User
):
    # user = database.get_user(user_id=event_from_user.id)

    # if user is None:
        await start(message, state, bot)
    # else:
    #     await main_menu(message, state, keyboards)


async def start(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    data = await state.get_data()

    start_message_id = data.get('start_message_id', None)
    if start_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=start_message_id
            )
        except TelegramBadRequest:
            pass
    
    start_message = await message.answer_video(
        video=start_video,
        caption=messages.start
    )
    bot_message = await message.answer(
        messages.enter_your_name
    )
    await state.update_data(
        main_menu_message_id=start_message.message_id, 
        start_message_id=start_message.message_id,
        del_messages=[bot_message.message_id]
    )
    await state.set_state(MainMenu.get_name)


# Confirm
@r.callback_query(
    ProfileSettings.location_confirm, 
    F.data == bt.confirm
)
async def get_current_location_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot,
    scheduler: EveryDayPredictionScheduler
):
    data = await state.get_data()
    
    name = data['name']
    current_location = data['current_location']
    current_location_title = data['current_location_title']

    if data['first_time']:
        birth_datetime = data['birth_datetime']
        birth_location = data['birth_location']
        birth_location_title = data['birth_location_title']
        
        now = datetime.utcnow()
        test_period_end = now + timedelta(
            days=subscription_test_period_in_days
        )
        database.add_user(
            DBUser(
                user_id=event_from_user.id,
                name=name,
                role='user',
                birth_datetime=birth_datetime,
                birth_location=Location(
                    type='birth', 
                    **birth_location,
                    title=current_location_title
                ),
                current_location=Location(
                    type='current',
                    **current_location,
                    title=birth_location_title
                ),
                subscription_end_date=test_period_end.strftime(
                    database_datetime_format
                ),
                timezone_offset=get_timezone_offset(
                    **current_location
                ),
                every_day_prediction_time='7:30'
            )
        )
        await scheduler.add_send_message_job(
            user_id=event_from_user.id, 
            database=database,
            bot=bot
        )
        await state.update_data(
            prediction_access=True,
            subscription_end_date=test_period_end.strftime(
                database_datetime_format
            )
        )
        await main_menu(
            callback.message, 
            state,
            keyboards,
            bot
        )
    else:
        database.update_user_current_location(
            event_from_user.id, 
            Location(
                id=0,
                type='current', 
                **current_location,
                title=get_location_by_coords(**current_location)
            )
        )
        await scheduler.edit_send_message_job(
            user_id=event_from_user.id, 
            database=database,
            bot=bot
        )
        await main_menu(
            callback.message, 
            state,
            keyboards,
            bot
        )


@r.message(Command(commands=['menu']))
async def main_menu_command(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot
):
    user = database.get_user(user_id=event_from_user.id)

    if user is None:
        bot_message = await message.answer(
            'Вы ещё не ввели данные рождения.'
        )
        await user_command_start_handler(bot_message, state, bot)
    else:
        await main_menu(message, state, keyboards, bot)


@r.message(
    MainMenu.predictin_every_day_choose_action, 
    F.text,
    F.text == bt.back
)
@r.message(
    F.text, 
    F.text == bt.main_menu
)
async def main_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    data = await state.get_data()
    main_menu_message_id = data.get(
        'main_menu_message_id',
        None
    )

    if main_menu_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, 
                message_id=main_menu_message_id
            )
        except TelegramBadRequest:
            pass

    if data['prediction_access']:
        keyboard = keyboards.main_menu
    else:
        keyboard = keyboards.main_menu_prediction_no_access

    if data['first_time']:
        main_menu_message = await message.answer(
            messages.main_menu_first_time,
            reply_markup=keyboard
        )
        await state.update_data(first_time=False)

    else:
        main_menu_message = await message.answer(
            messages.main_menu,
            reply_markup=keyboard
        )

    await state.update_data(
        del_messages=[message.message_id], 
        main_menu_message_id=main_menu_message.message_id
    )
    await state.set_state(MainMenu.choose_action)


@r.callback_query(
    F.data == bt.main_menu
)
@r.callback_query(
    Subscription.period,
    F.data == bt.back
)
async def to_main_menu_button_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    await main_menu(callback.message, state, keyboards, bot)


@r.message(F.text, F.text == bt.about_bot)
async def about_bot(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.about_bot,
        reply_markup=keyboards.to_main_menu
    )
    await state.update_data(del_messages=[bot_message.message_id])


# Всякая хуйня которую я ещё не написал
@r.callback_query(F.data.in_(not_implemented_list))
async def not_implemented_error_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    await not_implemented_error(
        callback.message,
        state,
        keyboards,
        bot
    )


# Всякая хуйня которую я ещё не написал
@r.message(F.text, F.text.in_(not_implemented_list))
async def not_implemented_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    bot_message = await message.answer(
        messages.not_implemented
    )
    await main_menu(bot_message, state, keyboards, bot)

