import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self, model: str):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY_NEW"))
        self.model_name = model
        
        #available options
        # self.model_name = "llama-3.1-8b-instant"
        # self.model_name = "qwen/qwen3-32b"
        # self.model_name = "llama-3.3-70b-Versatile"


    def generate(self, system_prompt, conversation):

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        for msg in conversation[-7:]:
            text = msg.get("text", "").strip()
            if not text:
                continue

            sender = msg.get("sender", "").lower()
            role = "assistant" if sender == "assistant" else "user"

            messages.append({
                "role": role,
                "content": text
            })

        # Ensure last message is user 
        while len(messages) > 1 and messages[-1]["role"] != "user":
            messages.pop()

        if len(messages) == 1:
            raise ValueError("Conversation must include at least one valid user message.")

        print("LLM CALLED\n", self.model_name)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )

        print(response.choices[0].message.content.strip())
        return response.choices[0].message.content.strip()
