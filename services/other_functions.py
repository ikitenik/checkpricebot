from config_data.config import Config, load_config
import aiosqlite
config: Config = load_config()



# Проверка, есть ли пользователь в базе данных
async def check_new_user(user_id : int) -> bool:
    async with aiosqlite.connect(config.db.database) as connection:
        async with connection.execute('select * from users where id = ?', (user_id,)) as cursor:
            check = await cursor.fetchall()
            if len(check) == 0:
                async with connection.execute('insert into users (id, state) values (?, ?)', (user_id, 0)):
                    await connection.commit()
                return True
            return False


# Проверка наличия отслеживаемых товаров
async def check_list(user_id):
    async with aiosqlite.connect(config.db.database) as connection:
        async with connection.execute('select * from products where user = ?', (user_id,)) as cursor:
            check = await cursor.fetchall()
            if len(check) == 0:
                return False
            return True


# Проверка, есть ли пользователь в базе данных
async def check_duplicate(user_id: int, recieved_url: str) -> bool:
    async with aiosqlite.connect(config.db.database) as connection:
        async with connection.execute('select url from products where user = ?', (user_id,)) as cursor:
            check = await cursor.fetchall()
    for i in range(len(check)):
        if check[i][0] == recieved_url:
            return True
    return False


# Исключение, выводяющее ошибку в случае, если вводимый айди меньше 0
class PositiveNumbers(Exception):
    def __init__(self, text):
        self.text = text
