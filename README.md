# TON Documentation + ChatGPT Telegram Bot

<div align="center">
<img src="https://ton.org/docs/img/ton_logo_dark_background.svg" align="center" style="width: 30%" />
</div>

<br>


Docster AI is a bot created to answer tech-related questions about TON Blockchain directly in Telegram ([@docster_bot](https://t.me/docster_bot))


## Vision

- [x] ChatGPT bot
- [x] TON Documentation added to knowledge index
- [x] TON Answers added to knowledge index
- [ ] TON Ecosystem GitHub repositories added to knowledge index
- [ ] Add more FunC examples to index to help with FunC errors
- [ ] Add bot to [TON Dev Chat](https://t.me/tondev_eng) and add `/ask@docster_bot` command there


## Bot commands
- `/retry` – Regenerate last bot answer
- `/new` – Start new dialog
- `/balance` – Show balance
- `/help` – Show help

## Setup
1. Get your [OpenAI API](https://openai.com/api/) key

2. Get your Telegram bot token from [@BotFather](https://t.me/BotFather)

3. Get your [Pinecone](https://pinecone.io/) API key & Environment to [work with your Docs index](https://www.youtube.com/watch?v=tBJ-CTKG2dM)

4. Edit `config/config.example.yml` to set your tokens and run 2 commands below (*if you're advanced user, you can also edit* `config/config.example.env`):
    ```bash
    mv config/config.example.yml config/config.yml
    mv config/config.example.env config/config.env
    ```

5. 🔥 And now **run**:
    ```bash
    docker-compose --env-file config/config.env up --build
    ```
