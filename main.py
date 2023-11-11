import asyncio
import sys
import logging

from src import main as bot_main


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(bot_main())


if __name__ == '__main__':
    main()

