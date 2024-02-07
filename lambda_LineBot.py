import os
import json
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import boto3

# Initialize LINE Bot API and WebhookHandler
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
quiz_questions_table = dynamodb.Table('QuizQuestions')
user_state_table = dynamodb.Table('UserStates')

def lambda_handler(event, context):
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text.lower()
        reply_token = event.reply_token
        
        user_state_response = user_state_table.get_item(Key={'UserID': user_id})
        user_state = user_state_response.get('Item', {})
        
        if user_state.get('QuizCompleted', True):
            if text != 'start quiz':
                line_bot_api.reply_message(reply_token, TextSendMessage(text="Please type 'start quiz' to begin the quiz."))
            else:
                send_first_question(user_id, reply_token)
        else:
            if text == 'start quiz' or user_state.get('QuestionID') is None:
                send_first_question(user_id, reply_token)
            else:
                handle_user_answer(user_id, text, user_state.get('QuestionID'), reply_token)

    
    signature = event['headers']['x-line-signature']
    body = event['body']
    handler.handle(body, signature)
    

def update_user_state(user_id, question_id=None, has_answered=False, quiz_completed=False):
    item = {
        'UserID': user_id,
        'HasAnswered': has_answered,
        'QuizCompleted': quiz_completed
    }
    if question_id is not None:
        item['QuestionID'] = question_id  

    user_state_table.put_item(Item=item)


def send_first_question(user_id, reply_token):
    response = quiz_questions_table.scan()
    questions = response.get('Items', [])
    questions_sorted = sorted(questions, key=lambda x: x['QuestionID'])
    if questions_sorted:
        question_item = next((q for q in questions_sorted if q['QuestionID'] == 1), None)
        if question_item:
            question_text = question_item['Question']
            options = question_item['Options']
            options_text = "\n".join([value for value in options.values()])
            update_user_state(user_id, question_item['QuestionID'], False)
            line_bot_api.reply_message(
                reply_token, [
                    TextSendMessage(text=question_text),
                    TextSendMessage(text=options_text)
                ]
            )

def handle_user_answer(user_id, text, current_question_id, reply_token):
    question_response = quiz_questions_table.get_item(Key={'QuestionID': current_question_id})
    if 'Item' in question_response:
        current_question = question_response['Item']
        options = current_question['Options']
        correct_answer = current_question['CorrectAnswer']
        reply_text = "Correct!" if text.upper() == correct_answer.upper() else f"Incorrect, The correct answer is {correct_answer}."
        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
        next_question_id = current_question_id + 1
        update_user_state(user_id, next_question_id, True)
        send_next_question(user_id, next_question_id)

def send_next_question(user_id, next_question_id):
    question_response = quiz_questions_table.get_item(Key={'QuestionID': next_question_id})
    
    if 'Item' in question_response:
        next_question = question_response['Item']
        update_user_state(user_id, next_question_id, False, False)
        question_text = next_question['Question']
        options = next_question['Options']
        options_text = "\n".join([value for value in options.values()])
        
        line_bot_api.push_message(
            user_id, [
                TextSendMessage(text=question_text),
                TextSendMessage(text=options_text)
            ]
        )
    else:
        final_message = "All questions have been answered. Type 'start quiz' to begin again."
        line_bot_api.push_message(user_id, TextSendMessage(text=final_message))
        update_user_state(user_id, None, False, True) 
            
   
