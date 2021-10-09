import telebot
from telebot import types
from dotenv import load_dotenv
import os
from db import Sql, AdminDB
import time

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
MIKAIL_ID = int(os.getenv("MIKAIL_ID"))
ABDULMALIK_ID = int(os.getenv("ABDULMALIK_ID"))



global bot
bot = telebot.TeleBot(API_TOKEN, parse_mode="html")

def in_mark(msg):
    in_mark = types.InlineKeyboardMarkup()
    if msg.text.upper() == "ГРУППА":
        return in_mark
    db = Sql(msg)
    abs_list = db.get_abscent_list(table_name=msg.text.upper())
    Addb = AdminDB()
    Addb.add_msg(msg)
    if abs_list:
        in_mark.add(types.InlineKeyboardButton("Добавить студента", callback_data=f"add_student{msg.text.upper()}"))
    if bool(len(db.cur.execute(f"SELECT * FROM {msg.text.upper()}").fetchall())):
        in_mark.add(types.InlineKeyboardButton("Удалить студента", callback_data=f"delete_student{msg.text.upper()}"))
    return in_mark

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    global bot
    return bot.send_message(chat_id, text, disable_notification=True, reply_markup=reply_markup, parse_mode=parse_mode)

def set_markup(msg, delete=False):
    db = Sql(msg)
    listt = db.get_list()
    if delete:
        listt = [el for el in listt if el != "ГРУППА"]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)    
    for el in listt:
        markup.row(types.KeyboardButton(el))
    return markup

def admin_list():
    db = AdminDB()
    admin_list = db.get_users_id()
    return admin_list

def inline(msg, table):
    db = Sql(msg)
    abs_list = db.get_abscent_list(table_name=table.upper())
    dictt = db.get_dict()
    markup = types.InlineKeyboardMarkup()
    for el in abs_list:
        markup.row(types.InlineKeyboardButton(dictt[el], callback_data=f"{el}/{table.upper()}/add_stud"))
    markup.row(types.InlineKeyboardButton("Готово", callback_data=f"Done/{table.upper()}"))
    return markup

def del_inline(msg, table):
    db = Sql(msg)
    stud_list = db.cur.execute(f"SELECT * FROM {table}").fetchall()
    markup = types.InlineKeyboardMarkup(row_width=3)
    dictt = db.get_dict()
    for el in stud_list:
        markup.add(types.InlineKeyboardButton(dictt[el[0]], callback_data=f"{el[0]}/{table.upper()}/del_stud"))
    markup.row(types.InlineKeyboardButton("Готово", callback_data=f"Done/{table.upper()}"))
    return markup
    
@bot.message_handler(commands=["delete_list", "add_list", "start", 'help', "setuser","newstudent", "delstudent"])
def delete_table_handler(msg):
    text = msg.text.lower()
    if msg.from_user.id not in admin_list():
        send_message(msg.chat.id, f"Вы не являетесь правовладельцем этого бота.\nПо нужным вопросам обращайтесь к @pythonist1")
        return
    db = Sql(msg)
    if text == "/start":
        if (not db.check_empty_table(table_name="ГРУППА")):
            bot.register_next_step_handler(send_message(msg.from_user.id, "Введите список ваших студентов через перенос строки\nПример:<b>\nРамазанов Гамид\nСаидов Рашид\nИсмаилов Магомед\nГаджиев Загир</b>"), start_2)
            return
        bot.reply_to(msg, "Список уже заполнен, повторить эту команду нельзя")
        return
    if (not db.check_empty_table(table_name="ГРУППА")):
        text = "Вы не можете пользоваться ботом пока не пополните список студентов вашей группы\nДля этого вводите /start"
        send_message(msg.chat.id, text)
        return
    if text == "/delete_list":
        listt = db.get_list()
        if len(listt) > 1:
            bot.register_next_step_handler(send_message(msg.chat.id, "Выберите список который хотите удалить", reply_markup=(set_markup(msg, delete=True))), delete_table_2)
            return
        send_message(msg.chat.id, "Нет списков, которые можно удалить\n/help", reply_markup=set_markup(msg))
    elif text == "/add_list":
        bot.register_next_step_handler(send_message(msg.chat.id, "Введите название для нового списка"), add_list_handler_2)
    
    elif text == "/help":
        text = "<b>Здесь можно облегчить работу с группой студентов</b>.\n\n<b>Основные команды:</b>\n    /add_list - Создать новый список.\n    /delete_list - Удалить существующий список.\n<b>Изменение главного списка</b>:\n    /newstudent - Добавить нового студента в главный список.\n    /delstudent - Удалить студента из главного cписка.\n\n    /help - Получить помощь по работе с ботом.\n\n<b>Для уточнения каких-либо вопросов обращайтесь к @IDeives.</b>"
        send_message(msg.chat.id, text, reply_markup=set_markup(msg))

    elif text == "/setuser":
        if msg.from_user.id != 1134958712:
            send_message(msg.chat.id, "Вам недоступная эта команда\n/help")
            return
        bot.register_next_step_handler(bot.send_message(msg.chat.id, "Введите имя и user_id нового пользователя через \\n"), set_user_2)

    elif text == "/newstudent":
        awaits = send_message(msg.chat.id, "Введите ФИО студента, которого хотите добавить в главный список", reply_markup=set_markup(msg))
        bot.register_next_step_handler(awaits, new_student_2)
        return
    
    elif text == "/delstudent":
        send_message(msg.chat.id, "Выберите студента, которого навсегда удалить из списка группы", reply_markup=del_inline(msg, "ГРУППА"))
    

@bot.message_handler(content_types=['text'])
def handlerr(msg):
    if msg.from_user.id not in admin_list():
        send_message(msg.chat.id, f"Вы не являетесь правовладельцем этого бота.\nПо нужным вопросам обращайтесь к @pythonist1")
        return
    DB = Sql(msg)
    if (not DB.check_empty_table(table_name="ГРУППА")):
        text = "Вы не можете пользоваться ботом пока не пополните список студентов вашей группы\nДля этого вводите /start"
        send_message(msg.chat.id, text)
        return
    listt = DB.get_list()
    if msg.text.upper() == "ГРУППА":
        send_message(msg.chat.id, f"<b>Список группы:</b>{DB.table_to_str('ГРУППА')}", reply_markup=set_markup(msg))
        return
    elif msg.text.upper() in listt:
        for el in listt:
            if el == msg.text.upper():
                send_message(msg.chat.id, DB.table_to_str(table_name=el), reply_markup=in_mark(msg))
                return
    else:
        send_message(msg.chat.id, "не знаю как на это ответить\n/help", reply_markup=set_markup(msg))
    
def add_list_handler_2(msg):
    db = Sql(msg)
    if len(msg.text.split()) == 1:
        if db.add_list(table_name=msg.text.upper()):
            send_message(msg.chat.id, f"Новый список <b>{msg.text.title()}</b> успешно добавлен", reply_markup=set_markup(msg))
            return
        send_message(msg.chat.id, f"Список {msg.text.upper()} уже сущетсвует", reply_markup=set_markup(msg))
        return
    awaits = send_message(msg.chat.id, "Неверно введённые данные, группа может являться только одним словом.\nПовторите попытку.")
    bot.register_next_step_handler(awaits, add_list_handler_2)

def delete_table_2(msg):
    db = Sql(msg)
    if msg.text.upper() != "ГРУППА":
        if db.delete_list(table_name=msg.text.upper()):
            send_message(msg.chat.id, f"Список {msg.text.title()} успешно удален", reply_markup=set_markup(msg))
            return
        bot.register_next_step_handler(send_message(msg.chat.id, f"Списка {msg.text.title()} не существует, выберите список из предоставленных в виде кнопок.", reply_markup=set_markup(msg)), delete_table_2)
        return
    send_message(msg.chat.id, "Нельзя удалить главный список \"ГРУППА\", но его можно обновить командами:\n/newstudent      /delstudent")
def set_user_2(msg):
    adb = AdminDB()
    adb.add_user(name=msg.text.split()[0], id=msg.text.split()[1])
    send_message(msg.chat.id, "Пользователь успешно добавлен в базу данных")

def start_2(msg):
    db = Sql(msg)
    db.add_student_main(data=msg)
    send_message(msg.chat.id, "Список студентов успешно добавлен.\nДля просмотра жмите на <b>\"ГРУППА\"</b>", reply_markup=set_markup(msg))
    time.sleep(2)
    text = "<b>Здесь можно облегчить работу с группой студентов</b>.\n\n<b>Основные команды:</b>\n    /add_list - Создать новый список.\n    /delete_list - Удалить существующий список.\n<b>Изменение главного списка:</b>\n    /newstudent - Добавить нового студента в главный список.\n    /delstudent - Удалить студента из главного группы.\n\n    /help - Получить помощь по работе с ботом.\n\n<b>Для уточнения каких-либо вопросов обращайтесь к @IDeives.</b>"
    send_message(msg.chat.id, text, reply_markup=set_markup(msg))
def new_student_2(msg):
    db = Sql(msg)
    table_list = db.get_table_list(table="ГРУППА")
    if msg.text not in table_list:
        db.add_student_main(data=msg)
        send_message(msg.chat.id, f"Студент {msg.text.strip()} успешно добавлен в главный список")
        return
    send_message(msg.chat.id, f"Студент {msg.text} уже в списке группы")
    return


@bot.callback_query_handler(func=lambda call: True)
def callback_handlerr(call):
    Admdb = AdminDB()
    msg = Admdb.get_msg()
    db = Sql(msg)
    dictt = db.get_dict()
    call_list = call.data.split('/')
    if "add_student" in call.data:
        table = call.data.replace("add_student", "")
        text = f"Выберите студента(ов), которого хотите добавить в список <b>{table.title()}</b>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=inline(msg, table))
        return
    if "Done" in call.data:
        table = call.data.split("/")[1]
        text = db.table_to_str(table)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_message(call.message.chat.id, text, reply_markup=in_mark(msg))
        return
    if "delete_student" in call.data:
        table = call.data.replace("delete_student", "")
        text = f"Выберите студента(ов), которых хотите удалить из списка <b>{table.title()}</b>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=del_inline(msg, table))
    for dataa in dictt:
        if str(dataa) == call_list[0]:
            table = call_list[1]
            table_list = db.get_table_list(table=table)
            if 'add_stud' == call_list[2]:
                if db.add_student_on_table(table, dataa):
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=inline(msg, table))
                    send_message(msg.chat.id, f"Студент {dictt[dataa]} успешно добавлен в список {table.title()}")
                    return
                if dictt[dataa] in table_list:
                    send_message(msg.chat.id, f"Студент {dictt[dataa]} уже в списке {table.title()}")
                    return
                send_message(msg.chat.id, f"Cтудента {dictt[dataa]} нет в списке {table.title()}")
            elif 'del_stud' == call_list[2]:
                if table == "ГРУППА":
                    if db.delete_student_main_table(id=dataa):
                        send_message(msg.chat.id, f"Студент {dictt[dataa]} успешно удалён из списка учащихся", reply_markup=set_markup(msg))
                        return
                    return
                if db.delete_student(table, dataa):
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=del_inline(msg, table))
                    send_message(msg.chat.id, f"Студент {dictt[dataa]} успешно удалён из списка {table.title()}")
                    return
                if db.check_student_exists_by_id(dataa, table="ГРУППА"):
                    send_message(msg.chat.id, f"Студент {dictt[dataa]} уже удалён из списка {table.title()}")
                    return
                send_message(msg.chat.id, f"Студента {dictt[dataa]} нет в списке {table.title()}")


if __name__ == "__main__":
    bot.infinity_polling()
