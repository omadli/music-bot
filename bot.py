import re
import os
from uzhits_parser import Uzhits
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.callback_data import CallbackData

API_TOKEN = os.environ.get('API_TOKEN') # for heroku
if API_TOKEN is None:
    # manual write api token
    API_TOKEN = "YOUR API TOKEN"

bot = Bot(token=API_TOKEN, parse_mode='html')
dp = Dispatcher(bot=bot)
muz = Uzhits()

btn_dl = CallbackData('dl', 'url')
btn_page = CallbackData('page', 'q', 's')

def build_keyboard(query: str, page: int = 1):
    buttons = []
    musics = muz.get_musics(query, page, (page-1)*10+1)
    # print(musics)
    if musics is not None and musics:
        for name, link in musics:
            music_link = re.match(r"https:\/\/uzhits.net\/(.+)\.html", link).group(1)
            buttons.append([types.InlineKeyboardButton(
                text=name,
                callback_data=btn_dl.new(url=music_link)
            )])
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
    link = muz.dl(message.text)
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
    music_link = muz.dl(link)
    await call.message.answer_audio(music_link, caption="🚀By @uzhits_music_bot")
    await call.answer()


@dp.callback_query_handler(btn_page.filter())
async def pagination(call: types.CallbackQuery, callback_data: dict):
    txt = call.message.text
    match = re.match(r".+ qidiruvi bo'yicha natijalar ([0-9]+)-([0-9]+) ([0-9]+) tadan", txt)
    s = int(match.group(1))
    n = int(match.group(3))
    page = int(callback_data['s'])
    q = callback_data['q']
    if page < 1:
        call.answer("Birinchi sahifadasiz", show_alert=True)
        return
    if n - s < 10:
        call.answer("Oxirgi sahifadasiz", show_alert=True)
        return
    s1 = (page-1)*10+1
    k = (s1 + 9) if (n // 10 + 1 > page) else (s1 + n % 10)
    await call.message.edit_text(f"<code>{q}</code> qidiruvi bo'yicha natijalar {s1}-{k} {n} tadan",
                             reply_markup=build_keyboard(q, page))

   
    
@dp.message_handler()
async def search_music(message: types.Message):
    n = muz.search_n(query=message.text)
    if n is not None and n:
        # topildi
        k = n if n < 10 else 10
        await message.answer(f"<code>{message.text}</code> qidiruvi bo'yicha natijalar 1-{k} {n} tadan",
                             reply_markup=build_keyboard(message.text))
    else:
        # topilmadi
        await message.answer("Hech narsa topilmadi 😔", 
                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                 [types.InlineKeyboardButton(text="❌", callback_data='del')]
                             ]))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
