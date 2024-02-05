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

# 初始化 LINE Bot API 和 WebhookHandler
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

# 初始化 DynamoDB 客户端
dynamodb = boto3.resource('dynamodb')
quiz_questions_table = dynamodb.Table('QuizQuestions')
user_state_table = dynamodb.Table('userstates')  #

def lambda_handler(event, context):
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text.lower()
        reply_token = event.reply_token
        if text == 'start quiz':
            # 從 DynamoDB 獲取問題
            response = quiz_questions_table.scan()  # 注意：生產環境應使用 query 而非 scan
            questions = response.get('Items', [])
            if questions:
                question_item = questions[0]  # 假設我們只取第一個問題
                question_text = question_item['questions']  
                options = question_item.get('Option', {})
                options_m = options.get('M', {})
                options_text = "\n".join([f"{key}: {value['S']}" for key, value in options_m.items()])

                reply_text = f"{question_text}\n{options_text}"
                update_user_state(user_id, question_item['question_id'])  # 更新用戶狀態
            else:
                reply_text = "No questions available."
        else:
            # 從 DynamoDB 獲取用戶狀態
            user_state_response = user_state_table.get_item(
                Key={'UserID': user_id}
            )
            user_state = user_state_response.get('Item', {})
            if not user_state:
                # 如果用戶狀態不存在，提示用戶開始問答
                reply_text = "Please send 'start quiz' to begin the quiz."
            else:
                current_question_id = user_state.get('QuestionID', None)
                # 獲取當前問題
                question_response = quiz_questions_table.get_item(
                    Key={'question_id': current_question_id}
                )
                current_question = question_response.get('Item', {})
                correct_answer = current_question.get('correct_answer', None)
                
                # 檢查用戶答案是否正確
                if text.upper() == correct_answer.upper():
                    reply_text = "Correct!"
                    # 此處應添加邏輯以更新到下一個問題或結束問答
                else:
                    reply_text = "Incorrect. Please try again."

        # 回覆用戶
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

def update_user_state(user_id, question_id):
    """
    更新用户状态，记录当前回答的问题ID。
    :param user_id: 用户的ID
    :param question_id: 当前问题的ID
    """
    try:
        # 使用 put_item 方法更新 DynamoDB 中的用户状态
        response = user_state_table.put_item(
            Item={
                'UserID': user_id,
                'QuestionID': question_id
            }
        )
        print(f"User state updated successfully: {response}")
    except Exception as e:
        print(f"Error updating user state: {e}")
