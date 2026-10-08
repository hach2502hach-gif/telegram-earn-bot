# Telegram Earn Bot

Первая версия бота: задания, автоматическая проверка подписки на канал, баланс, реферальная ссылка и заявки на вывод.

1. Создай бота через @BotFather.
2. Скопируй `.env.example` в `.env` и укажи BOT_TOKEN и ADMIN_ID.
3. Установи Python 3.11+ и выполни `pip install -r requirements.txt`.
4. Запусти `python bot.py`.
5. Для проверки подписки добавь бота администратором в нужный канал.

Важно: бот не предназначен для накрутки или имитации действий пользователей.


## Запуск на Render с телефона

1. Создай GitHub-репозиторий и загрузи сюда файлы проекта.
2. На Render выбери New → Web Service и подключи этот репозиторий.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. В Environment добавь:
   - `BOT_TOKEN` = токен BotFather
   - `ADMIN_ID` = твой Telegram ID
6. Нажми Deploy.

Не публикуй BOT_TOKEN в GitHub. Храни его только в Environment Variables Render.

Примечание: бесплатный Render Web Service может засыпать при отсутствии входящего трафика. Для стабильного Telegram polling позже лучше перенести бота на сервис с постоянным worker/background process или перевести код на webhook.
