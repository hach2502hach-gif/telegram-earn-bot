import asyncio, os, sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from dotenv import load_dotenv
load_dotenv()
TOKEN=os.getenv('BOT_TOKEN',''); ADMIN_ID=int(os.getenv('ADMIN_ID','0')); DB=os.getenv('DB_PATH','bot.db')
if not TOKEN: raise RuntimeError('Set BOT_TOKEN in .env')
bot=Bot(TOKEN); dp=Dispatcher(); db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
db.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT,balance REAL DEFAULT 0,referrer_id INTEGER,created_at TEXT);CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,url TEXT,reward REAL,channel_id TEXT,active INTEGER DEFAULT 1);CREATE TABLE IF NOT EXISTS completions(user_id INTEGER,task_id INTEGER,completed_at TEXT,PRIMARY KEY(user_id,task_id));CREATE TABLE IF NOT EXISTS withdrawals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,amount REAL,details TEXT,status TEXT DEFAULT 'pending',created_at TEXT);'''); db.commit()
def now(): return datetime.utcnow().isoformat(timespec='seconds')
def menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🎯 Задания',callback_data='tasks'),InlineKeyboardButton(text='💰 Баланс',callback_data='balance')],[InlineKeyboardButton(text='👥 Рефералы',callback_data='refs'),InlineKeyboardButton(text='💸 Вывод',callback_data='withdraw')]])
def reg(u,ref=None):
 if not db.execute('SELECT 1 FROM users WHERE id=?',(u.id,)).fetchone(): db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(u.id,u.username or '',0,ref if ref!=u.id else None,now())); db.commit()
def bal(uid): return float(db.execute('SELECT balance FROM users WHERE id=?',(uid,)).fetchone()['balance'])
@dp.message(CommandStart())
async def start(m:Message):
 a=(m.text or '').split(); ref=int(a[1]) if len(a)>1 and a[1].isdigit() else None; reg(m.from_user,ref); await m.answer('🔥 Добро пожаловать!\n\nВыполняй доступные задания, получай награды и приглашай друзей.',reply_markup=menu())
@dp.callback_query(F.data=='balance')
async def balance(c:CallbackQuery): await c.message.edit_text(f'💰 Баланс: <b>{bal(c.from_user.id):.2f}</b>',parse_mode='HTML',reply_markup=menu()); await c.answer()
@dp.callback_query(F.data=='refs')
async def refs(c:CallbackQuery):
 n=db.execute('SELECT COUNT(*) c FROM users WHERE referrer_id=?',(c.from_user.id,)).fetchone()['c']; me=await bot.get_me(); link=f'https://t.me/{me.username}?start={c.from_user.id}'; await c.message.edit_text(f'👥 Рефералов: <b>{n}</b>\n\nТвоя ссылка:\n<code>{link}</code>',parse_mode='HTML',reply_markup=menu()); await c.answer()
@dp.callback_query(F.data=='tasks')
async def tasks(c:CallbackQuery):
 rows=db.execute('SELECT * FROM tasks WHERE active=1 ORDER BY id DESC').fetchall(); buttons=[]
 for r in rows:
  if not db.execute('SELECT 1 FROM completions WHERE user_id=? AND task_id=?',(c.from_user.id,r['id'])).fetchone(): buttons.append([InlineKeyboardButton(text=f"🎯 {r['title']} +{r['reward']:.2f}",callback_data=f"task:{r['id']}")])
 buttons.append([InlineKeyboardButton(text='⬅️ Назад',callback_data='back')]); await c.message.edit_text('🎯 Доступные задания:' if rows else '🎯 Пока заданий нет.',reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()
@dp.callback_query(F.data.startswith('task:'))
async def task(c:CallbackQuery):
 tid=int(c.data.split(':')[1]); r=db.execute('SELECT * FROM tasks WHERE id=? AND active=1',(tid,)).fetchone()
 if not r: return await c.answer('Задание недоступно',show_alert=True)
 kb=[[InlineKeyboardButton(text='🔗 Открыть',url=r['url'])],[InlineKeyboardButton(text='✅ Проверить',callback_data=f'check:{tid}')],[InlineKeyboardButton(text='⬅️ К заданиям',callback_data='tasks')]]; await c.message.edit_text(f"<b>{r['title']}</b>\nНаграда: <b>{r['reward']:.2f}</b>",parse_mode='HTML',reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)); await c.answer()
async def subscribed(uid,ch):
 try: x=await bot.get_chat_member(ch,uid); return x.status in {ChatMemberStatus.MEMBER,ChatMemberStatus.ADMINISTRATOR,ChatMemberStatus.CREATOR}
 except: return False
@dp.callback_query(F.data.startswith('check:'))
async def check(c:CallbackQuery):
 tid=int(c.data.split(':')[1]); r=db.execute('SELECT * FROM tasks WHERE id=? AND active=1',(tid,)).fetchone()
 if not r: return await c.answer('Нет такого задания',show_alert=True)
 if db.execute('SELECT 1 FROM completions WHERE user_id=? AND task_id=?',(c.from_user.id,tid)).fetchone(): return await c.answer('Уже выполнено',show_alert=True)
 if r['channel_id'] and not await subscribed(c.from_user.id,r['channel_id']): return await c.answer('Сначала подпишись на канал.',show_alert=True)
 db.execute('INSERT INTO completions VALUES(?,?,?)',(c.from_user.id,tid,now())); db.execute('UPDATE users SET balance=balance+? WHERE id=?',(r['reward'],c.from_user.id)); db.commit(); await c.message.edit_text(f"✅ Выполнено!\nНачислено: <b>{r['reward']:.2f}</b>\nБаланс: <b>{bal(c.from_user.id):.2f}</b>",parse_mode='HTML',reply_markup=menu()); await c.answer()
@dp.callback_query(F.data=='withdraw')
async def wi(c:CallbackQuery): await c.message.edit_text(f"💸 Баланс: <b>{bal(c.from_user.id):.2f}</b>\n\nДля заявки:\n<code>/withdraw сумма реквизиты</code>",parse_mode='HTML',reply_markup=menu()); await c.answer()
@dp.message(Command('withdraw'))
async def withdraw(m:Message):
 p=(m.text or '').split(maxsplit=2)
 if len(p)<3: return await m.answer('Формат: /withdraw сумма реквизиты')
 try: amount=float(p[1])
 except: return await m.answer('Неверная сумма.')
 if amount<=0 or amount>bal(m.from_user.id): return await m.answer('Недостаточно средств.')
 db.execute('INSERT INTO withdrawals(user_id,amount,details,created_at) VALUES(?,?,?,?)',(m.from_user.id,amount,p[2],now())); db.commit(); await m.answer('✅ Заявка создана. Выплата после проверки.')
 if ADMIN_ID: await bot.send_message(ADMIN_ID,f'💸 Новая заявка\nUser: {m.from_user.id}\nСумма: {amount}\nРеквизиты: {p[2]}')
@dp.callback_query(F.data=='back')
async def back(c:CallbackQuery): await c.message.edit_text('Главное меню:',reply_markup=menu()); await c.answer()
async def main(): await dp.start_polling(bot)
if __name__=='__main__': asyncio.run(main())
