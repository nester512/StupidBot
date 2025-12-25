import asyncio

from src.main_polling import start_polling

if __name__ == '__main__':
    asyncio.run(start_polling())
