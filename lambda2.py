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

# 初始化 LINE Bot API 和 WebhookHandler
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

# 初始化 DynamoDB 客户端
dynamodb = boto3.resource('dynamodb')
quiz_questions_table = dynamodb.Table('QuizQuestions')
user_state_table = dynamodb.Table('userstates')  

def lambda_handler(event, context):
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text.lower()
        reply_token = event.reply_token
        
        # 获取用户状态
        user_state_response = user_state_table.get_item(Key={'UserID': user_id})
        user_state = user_state_response.get('Item', {})
        
        if text == 'start quiz' or not user_state:
            # 开始新的quiz或重新开始
            response = quiz_questions_table.scan()
            questions = response.get('Items', [])
            if questions:
                question_item = questions[0]  # 为简化，这里取第一个问题，你可以根据需要调整选择逻辑
                question_text = question_item['questions']
                options = question_item.get('option', {})
                options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
                reply_text = f"{question_text}\n{options_text}"
                question_id = question_item['question_id']
                update_user_state(user_id, question_id, False)  # 更新用户状态，指明他们正在回答哪个问题
            else:
                reply_text = "No questions available at the moment."
        else:
            current_question_id = user_state.get('question_id')
            if current_question_id:
                # 确保有一个有效的question_id来避免错误
                question_response = quiz_questions_table.get_item(Key={'question_id': current_question_id})
                current_question = question_response.get('Item', {})
                if current_question:
                    correct_answer = current_question.get('CorrectAnswer', '').lower()
                    if text == correct_answer:
                        reply_text = "Correct! The correct answer is: " + correct_answer
                        # 更新用户状态为没有正在回答的问题，准备下一个问题
                        update_user_state(user_id, "", True)
                        # 这里可以添加逻辑来获取并发送下一个问题
                    else:
                        reply_text = "Incorrect. Please try again, or type 'start quiz' to restart."
                else:
                    reply_text = "There was an error fetching the question. Please start the quiz again."
            else:
                reply_text = "No question found. Please start the quiz again."
                    
        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
    
    # 处理Webhook事件的代码部分保持不变
    signature = event['headers']['x-line-signature']
    body = event['body']
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }
    except LineBotApiError as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error handling message: {e}")
        }

    return {
        'statusCode': 200,
        'body': json.dumps("Hello from Lambda!")
    }




def update_user_state(user_id, question_id, has_answered=False):
    """
    更新用户状态，包括他们正在回答的问题的ID和是否已经回答了这个问题。
    :param user_id: 用户的ID
    :param question_id: 当前问题的ID
    :param has_answered: 用户是否已经回答了当前问题
    """
    try:
        response = user_state_table.put_item(
            Item={
                'UserID': user_id,
                'QuestionID': question_id,
                'HasAnswered': has_answered  # 新增字段，表示用户是否已回答
            }
        )
        print(f"User state updated successfully: {response}")
    except Exception as e:
        print(f"Error updating user state: {e}")
