import re
import os
# from uzhits_parser import Uzhits
from async_uzhits_parser import AsyncUzhits
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.callback_data import CallbackData
from slugify import slugify


HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
if HEROKU_APP_NAME is None:
    API_TOKEN = "YOUR API TOKEN"
    HEROKU = False

else:
    API_TOKEN = os.environ.get('API_TOKEN') # for heroku
    HEROKU = True

    # webhook settings
    WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
    WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
    WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

    # webserver settings
    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = os.getenv('PORT', default=8000)



bot = Bot(token=API_TOKEN, parse_mode='html')
dp = Dispatcher(bot=bot)
muz = AsyncUzhits()


async def on_startup(dispatcher: Dispatcher):
    await muz.start()
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print("Bot started")


async def on_shutdown(dispatcher: Dispatcher):
    await muz.close()
    await bot.delete_webhook()
    print("Bye")


btn_dl = CallbackData('dl', 'url')
btn_dl_by_id = CallbackData('music', 'id', 'row')
btn_page = CallbackData('page', 'q', 's')

async def build_keyboard(query: str, page: int = 1):
    buttons = []
    musics = await muz.get_musics(query, page, (page-1)*10+1)
    # print(musics)
    if musics is not None and musics:
        i = 0
        for name, link in musics:
            match = re.match(r"https:\/\/uzhits.net\/(.*)\/([0-9]+)(.+)\.html", link)
            music_id = match.group(2)
            music_link = music_id + match.group(3)
            btn = btn_dl.new(url=music_link)
            if len(music_link) > 50:
                btn = btn_dl_by_id.new(id=music_id, row=i)
            buttons.append([types.InlineKeyboardButton(
                text=name,
                callback_data=btn
            )])
            i += 1
    buttons.append([
        types.InlineKeyboardButton(text="⬅️", callback_data=btn_page.new(q=query, s=page-1)),
        types.InlineKeyboardButton(text="❌", callback_data='del'),
        types.InlineKeyboardButton(text="➡️", callback_data=btn_page.new(q=query, s=page+1)),
    ])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

        


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.answer(f"Assalomu alaykum {message.from_user.get_mention(as_html=True)}.\n"
                         f"Yordam menyusi /help")

    
@dp.message_handler(commands='help')
async def cmd_help(message: types.Message):
    await message.answer("Men sizga uzhits.net saytidan qo'shiqlarni qidirishga va yuklab olishga yordam beraman.\n"
                         "Qidirmoqchi bo'lgan biror qo'shig'ingizni yoki qo'shiqchini shunchaki nomini yozing.\n"
                         "Masalan <code>muhabbat</code>")


UZHITS_MUSIC_LINK = r"^https:\/\/uzhits\.net\/.+"
@dp.message_handler(regexp=UZHITS_MUSIC_LINK)
async def dl_music(message: types.Message):
    link = await muz.dl(message.text)
    print(link)
    await message.answer_audio(link, caption="🚀By @uzhits_music_bot")

@dp.callback_query_handler(text='del')
async def del_msg(call: types.CallbackQuery):
    await call.answer()
    await call.message.delete()


@dp.callback_query_handler(btn_dl.filter())
async def dl_music(call: types.CallbackQuery, callback_data: dict):
    link = 'https://uzhits.net/' + callback_data['url'] + '.html'
    # print(link)
    music_link = await muz.dl(link)
    await call.message.answer_audio(music_link, caption="🚀By @uzhits_music_bot")
    await call.answer()


@dp.callback_query_handler(btn_dl_by_id.filter())
async def dl_music(call: types.CallbackQuery, callback_data: dict):
    row = callback_data['row']
    music_id = callback_data['id']
    music_name = call.message.reply_markup.inline_keyboard[int(row)][0].text
    link = 'https://uzhits.net/mp3/' + music_id + '-' + slugify(music_name) + '.html'
    # print(link)
    music_link = await muz.dl(link)
    await call.message.answer_audio(music_link, caption="🚀By @uzhits_music_bot")
    await call.answer(music_name)


@dp.callback_query_handler(btn_page.filter())
async def pagination(call: types.CallbackQuery, callback_data: dict):
    txt = call.message.text
    match = re.match(r".+ qidiruvi bo'yicha natijalar ([0-9]+)-([0-9]+) ([0-9]+) tadan", txt)
    s = int(match.group(1))
    n = int(match.group(3))
    page = int(callback_data['s'])
    q = callback_data['q']
    if page < 1:
        await call.answer("Birinchi sahifadasiz", show_alert=True)
        return
    if page > ((n-1) // 10 + 1):
        await call.answer("Oxirgi sahifadasiz", show_alert=True)
        return
    s1 = (page-1)*10+1
    k = (s1 + 9) if (n // 10 + 1 > page) else (s1 + n % 10)
    await call.message.edit_text(f"<code>{q}</code> qidiruvi bo'yicha natijalar {s1}-{k} {n} tadan",
                             reply_markup=await build_keyboard(q, page))
    await call.answer(f"{page}-sahifa")

   
    
@dp.message_handler()
async def search_music(message: types.Message):
    try:
        n = await muz.search_n(query=message.text)
        if n is not None and n:
            # topildi
            k = n if n < 10 else 10
            await message.answer(f"<code>{message.text}</code> qidiruvi bo'yicha natijalar 1-{k} {n} tadan",
                                reply_markup=await build_keyboard(message.text))
        else:
            # topilmadi
            await message.answer("Hech narsa topilmadi 😔", 
                                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                    [types.InlineKeyboardButton(text="❌", callback_data='del')]
                                ]))
    except Exception as e:
        print(e)
        await message.answer("Hech narsa topilmadi 😔", 
                            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                [types.InlineKeyboardButton(text="❌", callback_data='del')]
                            ]))

async def on_startup_polling(dp):
    await muz.start()
    print('Bot started')
    
async def on_shutdown_polling(dp):
    await muz.close()
    print("Bye")
    

if __name__ == '__main__':
    if HEROKU:
        executor.start_webhook(
            dp,
            webhook_path=WEBHOOK_PATH,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT
        )
    else:
        executor.start_polling(
            dp, 
            skip_updates=True, 
            on_startup=on_startup_polling, 
            on_shutdown=on_shutdown_polling
        )
