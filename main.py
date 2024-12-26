from typing import Annotated
import os
from click import prompt
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import openai
from fastapi import FastAPI, Form, Request, WebSocket
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory='templates')

chat_Response = []

openai.api_key = os.getenv("OPENAI_API_SECRET_KEY")

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html",{"request": Request, "chat+Response":chat_Response})

chat_log = [{'role':'system', 'content':'You are a Python Tutor AI, completely dedicated to teach users how to learn Python from scratch, \
                                        Please provide detailed instructions on Python concepts, best practices and syntax. \
                                        Help users a path of learning for users to be able to create real life production ready Python application'}]

@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role':'user', 'content': user_input})
        chat_Response.append(user_input)

        try:
            response = openai.ChatCompletion.create(
                model = 'gpt-4',
                messages = chat_log,
                temperature = 0.6,
                stream = True
            )
            ai_response = ''
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response+=chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)
            chat_Response.append(ai_response)
        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break

@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({'role':'user', 'content':user_input})
    chat_Response.append(user_input)
    response = openai.ChatCompletion.create(
        model = 'gpt-4',
        messages = chat_log,
        temperature=0.6
    )

    bot_response = response['choices'][0]['message']['content']
    chat_log.append({'role':'assistant', 'content':bot_response})
    chat_Response.append(bot_response)
    return templates.TemplateResponse("home.html", {"request":request, "chat_Response":chat_Response})

@app.get("/image", response_class=HTMLResponse)
async def mage_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})

@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):
    response = openai.Image.create(
        prompt=user_input,
        n=1,
        size="256x256"
    )
    image_url = response['data'][0]['url']
    return templates.TemplateResponse("image.html", {"request":request, "image_url":image_url})