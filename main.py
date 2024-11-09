import requests
import time
import random
import sqlite3
from concurrent.futures import ThreadPoolExecutor


# Функция для сохранения данных в базу данных
def save_to_db(db_connection, email, ip):
    cursor = db_connection.cursor()
    
    # Проверяем, существует ли уже запись с таким email
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        # Если запись существует, обновляем IP
        cursor.execute("UPDATE users SET ip = ? WHERE email = ?", (ip, email))
    else:
        # Если записи нет, вставляем новую
        cursor.execute("INSERT INTO users (email, ip) VALUES (?, ?)", (email, ip))
    
    db_connection.commit()


# Функция для создания базы данных и таблицы
def create_database():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            ip TEXT NOT NULL
        )
    ''')
    connection.commit()
    return connection


# Функция для проверки прокси
def check_proxy(proxy):
    try:
        response = requests.get('http://httpbin.org/ip', proxies={"http": "http://"+ proxy.origin(), "https": "https://"+proxy.origin()}, timeout=5)
        if response.status_code == 200:
            return proxy, response.json()['origin']
    except requests.RequestException:
        return proxy, None
    return proxy, None

# Функция для работы с пользователями
def process_user(proxy_list, email, password, db_connection):
    # Выбор случайного прокси
    while True:
        i = random.randint(0, len(proxy_list))
        result = check_proxy(proxy_list[i])
        if result[1]:  # Если прокси работает
            proxy = proxy_list.pop(i)
            log_entry = f"Email: {email}, IP: {proxy.ip}:{proxy.port}"
            print(log_entry)  # Печать в консоль
            with open("proxy_log.txt", "a") as log_file:
                log_file.write(log_entry + "n")
            save_to_db(db_connection, email, f'{proxy.ip}:{proxy.port}')
            break
            
        #если не работает еще пробуем
        time.sleep(5)
    
        


class User:
    def __init__(self, email='', passw=''):
        self.email=email
        self.passw=passw
    @staticmethod
    def read_from_file(filename):
        data = []
        with open(filename, 'r') as file:
            for line in file:
                data.append(User(*line.split(':')))
        return data

class Proxy:
    def __init__(self, ip='', port='', user='', passw=''):
        self.ip=ip
        self.port=port
        self.user=user
        self.passw=passw
    def origin(self):
        return f'{self.user}:{self.passw}@{self.ip}:{self.port}'

    @staticmethod
    def read_from_file(filename):
        data = []
        with open(filename, 'r') as file:
            for line in file:
                data.append(Proxy(*line.split(':')))
        return data


# Список пользователей (email и password)
users = User.read_from_file('users.txt') #email:passw

def main():
    # Создаем базу данных и таблицу
    db_connection = create_database()
    
    while True:
        # Список прокси для проверки
        
        proxy_list = Proxy.read_from_file('proxy.txt') #ip:port:user:passw
    # Обработка каждого пользователя в отдельном потоке
        with ThreadPoolExecutor(max_workers=len(users)) as executor:
            for user in users:
                executor.submit(process_user, proxy_list, user.email, user.passw, db_connection)
        time.sleep(60)  # Ждем 1 минуту перед обновлением прокси

if __name__ == '__main__':
    main()
