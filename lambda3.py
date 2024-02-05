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
        
        # 检查用户状态以确定是否需要发送新问题或者提示用户当前问题的答案
        user_state_response = user_state_table.get_item(Key={'UserID': user_id})
        user_state = user_state_response.get('Item', {})
        
        if text == 'start quiz' or not user_state:
            # 从 DynamoDB 获取问题
            response = quiz_questions_table.scan()  # 注意：生产环境应使用 query 而非 scan
            questions = response.get('Items', [])
            if questions:
                question_item = questions[0]  # 假设我们只取第一个问题
                question_text = question_item['questions']
                options = question_item.get('Option', {})
                options_m = options.get('M', {})
                options_text = "\n".join([f"{key}: {value['S']}" for key, value in options_m.items()])
                reply_text = f"{question_text}\n{options_text}"
                # 直接获取question_id的值
                question_id = question_item['QuestionID']
                update_user_state(user_id, question_id, False)  
            else:
                reply_text = "Congratulations, You Complete the Exam!!!"
        elif user_state and not user_state.get('HasAnswered', True):
            current_question_id = user_state.get('QuestionID', '')
            question_response = quiz_questions_table.get_item(Key={'question_id': current_question_id})
            current_question = question_response.get('Item', {})
            correct_answer = current_question.get('correct_answer', {}).get('S', '').lower()
            
            if text == correct_answer:
                reply_text = "Correct!"
                # 此处应添加逻辑以更新到下一个问题或结束问答
            else:
                reply_text = "Incorrect. Please try again."
                
        # 回复用户
        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
        
    # get X-Line-Signature header value
    signature = event['headers']['x-line-signature']
    # get request body as text
    body = event['body']
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
        }
    except LineBotApiError as e:
        print(f"Error: {e}")
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
