# TON Documentation + ChatGPT Telegram Bot

<div align="center">
<img src="https://ton.org/docs/img/ton_logo_light_background.svg" align="center" style="width: 100%" />
</div>

<br>

_TODO_

## Bot commands
- `/retry` – Regenerate last bot answer
- `/new` – Start new dialog
- `/balance` – Show balance
- `/help` – Show help

## Setup
1. Get your [OpenAI API](https://openai.com/api/) key

2. Get your Telegram bot token from [@BotFather](https://t.me/BotFather)

3. Edit `config/config.example.yml` to set your tokens and run 2 commands below (*if you're advanced user, you can also edit* `config/config.example.env`):
    ```bash
    mv config/config.example.yml config/config.yml
    mv config/config.example.env config/config.env
    ```

4. 🔥 And now **run**:
    ```bash
    docker-compose --env-file config/config.env up --build
    ```
