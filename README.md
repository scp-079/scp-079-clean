# SCP-079-CLEAN

This bot is used to auto delete specific types of messages.

## How to use

- See [manual](https://telegra.ph/SCP-079-CLEAN-12-04)
- See [this article](https://scp-079.org/clean/) to build a bot by yourself
- Discuss [group](https://t.me/SCP_079_CHAT)

## To Do List

- [x] Basic functions
- [x] /dafm
- [x] /purge

## Requirements

- Python 3.6 or higher
- Debian 10: `sudo apt update && sudo apt install libzbar0 opencc -y`
- pip: `pip install -r requirements.txt` or `pip install -U APScheduler emoji OpenCC Pillow pyAesCrypt pyrogram[fast] pyzbar`

## Files

- plugins
    - functions
        - `channel.py` : Functions about channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `image.py` : Functions about image
        - `receive.py` : Receive data from exchange channel
        - `telegram.py` : Some telegram functions
        - `tests.py` : Some test functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user and channel object
    - handlers
        - `command.py` : Handle commands
        - `message.py`: Handle messages
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configuration
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
