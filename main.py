import asyncio
import logging

from src import main as bot_main


def main():
    logging.basicConfig(level=0)
    asyncio.run(bot_main())


if __name__ == '__main__':
    main()

