import config
import requests
import re
import tiktoken
import openai
import pinecone
openai.api_key = config.openai_api_key
CHAT_MODES = config.chat_modes


OPENAI_COMPLETION_OPTIONS = {
    "temperature": 0.0,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0.3,
    "presence_penalty": 0
}


class ChatGPT:
    def __init__(self, use_chatgpt_api=True):
        self.use_chatgpt_api = use_chatgpt_api
    
    async def send_message(self, message, dialog_messages=[], chat_mode="assistant"):
        if chat_mode not in CHAT_MODES.keys():
            raise ValueError(f"Chat mode {chat_mode} is not supported")

        n_dialog_messages_before = len(dialog_messages)
        answer = None
        attempts = 0
        while answer is None:
            try:
                messages = self._generate_prompt_from_index(message, chat_mode)

                res = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    **OPENAI_COMPLETION_OPTIONS
                )

                answer = res['choices'][0]['message']['content']
                n_used_tokens = self._count_tokens_for_chatgpt(messages, answer, model="gpt-3.5-turbo")

                answer = self._postprocess_answer(answer)

                # check for answer truth
                if answer.find('https://') > 0:
                    print('Sources found in answer:')
                    print(answer)
                    urls = re.findall(r'\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b', answer)

                    for url in urls:
                        res = requests.get(url)
                        if res.status_code != 200:
                            print(f"{res.status_code} for URL in answer: '{url}'")
                            answer = None
                            break

                # break infinity loop for 404 answers
                if answer is None:
                    attempts += 1

                if attempts > 3:
                    raise ValueError("Sorry, Docster AI provides too many fake links for this request! 🤪 Please, share info with @SwiftAdviser")

            except openai.error.InvalidRequestError as e:  # too many tokens
                if len(dialog_messages) == 0:
                    raise ValueError("Dialog messages is reduced to zero, but still has too many tokens to make completion") from e

                # forget first message in dialog_messages
                dialog_messages = dialog_messages[1:]

        n_first_dialog_messages_removed = n_dialog_messages_before - len(dialog_messages)

        return answer, n_used_tokens, n_first_dialog_messages_removed

    async def send_message_stream(self, message, dialog_messages=[], chat_mode="assistant"):
        if chat_mode not in CHAT_MODES.keys():
            raise ValueError(f"Chat mode {chat_mode} is not supported")

        n_dialog_messages_before = len(dialog_messages)
        answer = None
        while answer is None:
            try:
                if self.use_chatgpt_api:
                    messages = self._generate_prompt_from_index(message, chat_mode)
                    r_gen = await openai.ChatCompletion.acreate(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        stream=True,
                        **OPENAI_COMPLETION_OPTIONS
                    )

                    answer = ""
                    async for r_item in r_gen:
                        delta = r_item.choices[0].delta
                        if "content" in delta:
                            answer += delta.content
                            yield "not_finished", answer

                    n_used_tokens = self._count_tokens_for_chatgpt(messages, answer, model="gpt-3.5-turbo")

                answer = self._postprocess_answer(answer)

            except openai.error.InvalidRequestError as e:  # too many tokens
                if len(dialog_messages) == 0:
                    raise ValueError("Dialog messages is reduced to zero, but still has too many tokens to make completion") from e

                # forget first message in dialog_messages
                dialog_messages = dialog_messages[1:]

        n_first_dialog_messages_removed = n_dialog_messages_before - len(dialog_messages)

        yield "finished", answer, n_used_tokens, n_first_dialog_messages_removed  # sending final answer

    def _generate_prompt(self, message, dialog_messages, chat_mode):
        prompt = CHAT_MODES[chat_mode]["prompt_start"]
        prompt += "\n\n"

        # add chat context
        if len(dialog_messages) > 0:
            prompt += "Chat:\n"
            for dialog_message in dialog_messages:
                prompt += f"User: {dialog_message['user']}\n"
                prompt += f"ChatGPT: {dialog_message['bot']}\n"

        # current message
        prompt += f"User: {message}\n"
        prompt += "ChatGPT: "

        return prompt

    def _generate_prompt_from_index(self, message, chat_mode):


        # system message to 'prime' the model
        primer = CHAT_MODES[chat_mode]["prompt_start"]

        # pinecone index
        index_name = config.pinecone_index_name
        embed_model = 'text-embedding-ada-002'

        # initialize connection to pinecone
        pinecone.init(
            api_key=config.pinecone_api_key,  # app.pinecone.io (console)
            environment=config.pinecone_env  # next to API key in console
        )
        # connect to index
        index = pinecone.GRPCIndex(index_name)

        # query = "how do I use the FunC in TON Blockchain?"
        query = message

        # transform text to vector
        res = openai.Embedding.create(
            input=[query],
            engine=embed_model
        )

        # retrieve from Pinecone
        xq = res['data'][0]['embedding']

        # get relevant contexts (including the questions)
        res = index.query(xq, top_k=5, include_metadata=True)

        # get list of retrieved text
        contexts = [(item['metadata']['text'] + "\nSource: " + item['metadata']['url']) for item in res['matches']]

        augmented_query = "\n\n---\n\n".join(contexts) + "\n\n-----\n\n" + query

        messages = [
            {"role": "system", "content": primer},
            {"role": "user", "content": augmented_query}
        ]

        return messages

    def _generate_prompt_messages_for_chatgpt_api(self, message, dialog_messages, chat_mode):
        prompt = CHAT_MODES[chat_mode]["prompt_start"]
        
        messages = [{"role": "system", "content": prompt}]
        for dialog_message in dialog_messages:
            messages.append({"role": "user", "content": dialog_message["user"]})
            messages.append({"role": "assistant", "content": dialog_message["bot"]})
        messages.append({"role": "user", "content": message})

        return messages

    def _postprocess_answer(self, answer):

        answer = answer.strip()
        return answer

    def _count_tokens_for_chatgpt(self, prompt_messages, answer, model="gpt-3.5-turbo"):
        prompt_messages += [{"role": "assistant", "content": answer}]        

        encoding = tiktoken.encoding_for_model(model)
        n_tokens = 0
        for message in prompt_messages:
            n_tokens += 4  # every message follows "<im_start>{role/name}\n{content}<im_end>\n"
            for key, value in message.items():            
                if key == "role":
                    n_tokens += 1
                elif key == "content":
                    n_tokens += len(encoding.encode(value))
                else:
                    raise ValueError(f"Unknown key in message: {key}")
                    
        n_tokens -= 1  # remove 1 "<im_end>" token          
        return n_tokens

    def _count_tokens_for_gpt(self, prompt, answer, model="text-davinci-003"):
        encoding = tiktoken.encoding_for_model(model)
        n_tokens = len(encoding.encode(prompt)) + len(encoding.encode(answer)) + 1
        return n_tokens


async def transcribe_audio(audio_file):
    r = await openai.Audio.atranscribe("whisper-1", audio_file)
    return r["text"]