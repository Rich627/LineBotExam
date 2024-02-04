# main.py
from flask import Flask, request, abort
from quiz import Quiz
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from linebot import LineBotApi, WebhookHandler
from aws_wsgi import WSGIAdapter
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# 初始化 Quiz 和 Line Bot API
quiz = Quiz("/Users/rich/Desktop/ExamProject/ExamTopicsQuizMaker/res")
line_bot_api = LineBotApi('6ma2/BMmTTsYgegKkkzuRv34v3NRmyDzsxWFhg+/RyHwY4OfMWoFkK71vjcREuYI5tF7SuT7fYue8qWHBULwL6hs1ypXr+9tM+gV7Qdh4iaPn6MSM5v4srpj+wrUXrMzdTaYPnheVSNaVDE9pMysagdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('75636eab983915d02d1df6cfe2ad314e')

# 用戶會話類，用於追踪每個用戶的狀態
class UserSession:
    def __init__(self):
        self.in_quiz = False
        self.current_question_index = 0
        self.correct_answers = 0

user_sessions = {}
def lambda_handler(event, context):
    return WSGIAdapter(app).handle(event, context)

def handle_quiz_message(event, quiz, user_session):
    user_message = event.message.text
    response_message = "test"

    app.logger.info(f"Received user message: {user_message}")

    if user_message.lower() == 'start quiz':
        app.logger.info("User wants to start a quiz.")
        user_session.in_quiz = True
        response_message = quiz.start_quiz(user_session)
    elif user_session.in_quiz:
        app.logger.info("User is in a quiz. Handling the answer.")
        response_message = quiz.answer_question(user_session, user_message)
    else:
        app.logger.info("User's message is not related to the quiz.")

    return TextSendMessage(text=response_message)

@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        return 'Internal Server Error', 500
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()

    user_session = user_sessions[user_id]
    response_message = handle_quiz_message(event, quiz, user_session)

    if response_message:
        line_bot_api.reply_message(event.reply_token, response_message)
        app.logger.info(f"Replied with message: {response_message.text}")
    else:
        app.logger.error("handle_quiz_message did not return a valid response.")

if __name__ == '__main__':
    app.run()


