import pickle
import sqlite3
from sqlite3.dbapi2 import Error



class Sql:
    def __init__(self, msg) -> None:
        self.conn = sqlite3.connect(f"{msg.from_user.id}.db")
        self.cur = self.conn.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS ГРУППА (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data VARCHAR(255)
        )""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS list_dict (
            listt BLOB,
            dictt BLOB
        )""")

        self.conn.commit()

    def table_to_str(self, table_name: str):
        table_name = table_name.upper()
        result = f"<b>Список {table_name.title()}:</b>" if table_name.upper() != "ГРУППА" else ""
        if self.check_empty_table(table_name=table_name):
            exec = self.cur.execute(f"SELECT * FROM {table_name}").fetchall()
            all_stud = self.cur.execute(f"SELECT * FROM ГРУППА").fetchall()
            absent_list = self.get_abscent_list(table_name)
            dictt = self.get_dict()
            for i in all_stud:    
                for el in exec:    
                    if i[0] == el[0]:
                        result += f"\n    {el[0]}. {i[1]}"
            result += f"\n<b>Всего: {len(exec)}</b>"
            if absent_list:
                result += "<b>\nОтсутсвующие:</b>"
                for id in absent_list:
                    result += f"\n    {id}. {dictt[int(id)]}"
            return result
        return "\nСписок пуст"

    def delete_student_main_table(self, id: int):
        self.cur.execute(f"DELETE FROM ГРУППА WHERE id=?", (id,))
        self.conn.commit()
        self.set_dict()
        return True

    def add_student_main(self, data):
        for el in data.text.split("\n"):
            self.cur.execute("INSERT INTO ГРУППА(data) VALUES(?)", (el,))
        self.conn.commit()
        self.set_dict()
        return True

    def set_dict(self):
        dictt = {}
        res = self.cur.execute("SELECT * FROM ГРУППА").fetchall()
        for el in res:
            dictt[el[0]] = el[1]
        self.update_table_lists(dictt=dictt)
        return True

    def update_dictt(self, dictt):
        with self.conn:    
            self.cur.execute("UPDATE list_dict SET dictt=?", (pickle.dumps(dictt),))
            self.conn.commit()
            return True

    def add_to_list_students(self, data: str):
        with self.conn:
            data = data.split("\n")
            for el in data:
                self.cur.execute(f"INSERT INTO ГРУППА VALUES(?)", (el,))
                self.conn.commit()
            return True
    
    def add_list(self, table_name: str):
        table_name = table_name.upper()
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name.upper()} (
            id INT PRIMARY KEY,
            data VARCHAR(255)
        )""")
        self.conn.commit()
        listt = self.get_list()
        if table_name not in listt:
            listt.append(table_name.upper())
            self.update_table_lists(listt=listt)
            return True # f"Список {table_name} успешно создан"
        return False # f"Список {table_name} уже сущетсвует" 
    
    def delete_list(self, table_name: str):
        table_name = table_name.upper()
        listt = self.get_list()
        if table_name.upper() in listt:
            self.cur.execute(f"DROP TABLE IF EXISTS {table_name.upper()}")
            self.conn.commit()
            listt.remove(table_name.upper())
            self.update_table_lists(listt=listt)
            return True # f"Список {table_name} успешно удалён."
        return False
    
    def check_empty_table(self, table_name: str):
        table_name = table_name.upper()
        result = self.cur.execute(f"SELECT * FROM {table_name.upper()}").fetchall()
        return bool(len(result))

    def get_list(self):
        listt = self.cur.execute("SELECT listt FROM list_dict").fetchone()[0]
        try:
            return pickle.loads(listt)
        except TypeError:
            return ["ГРУППА"]

    def add_student_on_table(self,table_name, id: int):
        table_name = table_name.upper()
        dictt = self.get_dict()
        if (not self.check_student_exists_by_id(id,table_name)):
            self.cur.execute(f"INSERT INTO {table_name.upper()} VALUES (?,?)",(id, dictt[id]))
            self.conn.commit()
            return True
        return False

    def check_student_exists_by_id(self, id, table):
        table = table.upper()
        res = self.cur.execute(f"SELECT * FROM {table} WHERE id=?", (id,)).fetchall()
        return bool(len(res))

    def delete_student(self, table_name, id):
        table_name = table_name.upper()
        if self.check_student_exists_by_id(id, table=table_name):
            self.cur.execute(f"DELETE FROM {table_name.upper()} WHERE id=?", (id,))
            self.conn.commit()
            return True # f"Студент успешно удалён"
        return False # f"Студента с таким id нет в списке"

    def get_table_list_id(self, table):
        result = []
        table = table.upper()
        res = self.cur.execute(f"SELECT id FROM {table}").fetchall()
        for el in res:
            result.append(int(el[0]))
        return result # array if students id

    def get_table_list(self, table=None):
        if table is None:
            table = "ГРУППА"
        result = []
        table = table.upper()
        res = self.cur.execute(f"SELECT data FROM {table}").fetchall()
        for el in res:
            result.append(el[0])
        return result #array of students names

    def get_dict(self):
        try:
            dictt = self.cur.execute("SELECT dictt FROM list_dict").fetchone()[0]
        except TypeError:
            return {}
        if dictt is None:
            self.update_table_lists(dictt={})
            return {}
        return pickle.loads(dictt)

    def check_listt(self):
        res = self.cur.execute("SELECT listt FROM list_dict").fetchone()
        if not (res is None):
            return bool(len(res))
        return False

    def check_dict(self):
        res = self.cur.execute("SELECT dictt FROM list_dict").fetchone()
        if not(res is None):
            return bool(len(res))
        return False
        
    def update_table_lists(self, listt=False, dictt=False):
        if listt and dictt:
            self.cur.execute("UPDATE list_dict SET listt=?, dictt=?",(pickle.dumps(listt), pickle.dumps(dictt)))
            self.conn.commit()
            return True
        elif listt:
            if self.check_listt():
                self.cur.execute("UPDATE list_dict SET listt=?",(pickle.dumps(listt),))
                self.conn.commit()
                return True
            self.cur.execute("INSERT INTO list_dict(listt) VALUES(?)", (pickle.dumps(listt),))
            self.conn.commit()
            return True
        elif dictt:
            if self.check_dict():
                self.cur.execute("UPDATE list_dict SET dictt=?", (pickle.dumps(dictt),))
                self.conn.commit()
                return True
            self.cur.execute("INSERT INTO list_dict(dictt) VALUES(?)", (pickle.dumps(dictt),))
            self.conn.commit()
            return True

    def get_abscent_list(self, table_name):
        result = []
        list_ = []
        dictt = self.get_dict()
        for exec in self.cur.execute(f"SELECT * FROM {table_name.upper()}").fetchall():
            list_.append(exec[0])
        for id in dictt:
            if id not in list_:
                result.append(id)
        return result #absent_list: [5,16,28]
            
    



class AdminDB:
    def __init__(self) -> None:
        self.conn = sqlite3.connect("AdminDatabase.db")
        self.cur = self.conn.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS id_list (
            name VARCHAR(255),
            id INT
        )""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS message (
            msg BLOB
        )""")
        
        self.conn.commit()

        self.add_user(name='Admin', id=1134958712)

    def add_msg(self, msg):
        if self.cur.execute("SELECT msg FROM message").fetchone() is None:
            self.cur.execute("INSERT INTO message(msg) VALUES(?)", (pickle.dumps(msg),))
            self.conn.commit()
            return
        self.cur.execute("UPDATE message SET msg=?", (pickle.dumps(msg),))
        self.conn.commit()
        return

    def get_msg(self):
        msg = self.cur.execute("SELECT msg FROM message").fetchone()[0]
        return pickle.loads(msg)

    def check_user_exists(self, id):
        res = self.cur.execute("SELECT * FROM id_list WHERE id=?", (id,)).fetchall()
        return bool(len(res))

    def add_user(self, name, id):
        with self.conn:
            if (not self.check_user_exists(id=id)):
                self.cur.execute("""INSERT INTO id_list VALUES (?,?)""", (name, id))
                return True
            return False
    
    def get_users_id(self):
        ready_list = []
        result = self.cur.execute("SELECT id FROM id_list").fetchall()
        for el in result:
            ready_list.append(el[0])
        return ready_list
