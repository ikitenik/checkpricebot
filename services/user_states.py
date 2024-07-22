from config_data.config import Config, load_config
import aiosqlite
config: Config = load_config()

class UserState:
    NO = 0
    ADD = 1
    DEL = 2
    CHECK = 3


async def set_state(user_id, state):
    async with aiosqlite.connect(config.db.database) as connection:
        async with connection.execute('UPDATE users SET state = ? WHERE id = ?',
                   (state, user_id)):
            await connection.commit()


async def get_state(user_id):
    async with aiosqlite.connect(config.db.database) as connection:
        async with connection.execute('select state from users where id = ?', (user_id,)) as cursor:
            state = await cursor.fetchall()
    return state[0][0]
