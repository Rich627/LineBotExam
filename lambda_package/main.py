# main.py
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 初始化 Line Bot API
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

def lambda_handler(event, context):
    # 解析 API Gateway 传递的请求体
    body = event['body']
    signature = event['headers'].get('X-Line-Signature')

    # 尝试处理 Line Webhook 事件
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {'statusCode': 403, 'body': 'Invalid signature'}
    except LineBotApiError as e:
        return {'statusCode': 500, 'body': 'Internal server error'}

    return {'statusCode': 200, 'body': 'OK'}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 这里添加处理接收到的消息的逻辑
    # 例如，回复用户发送的相同消息
    text = event.message.text
    reply_token = event.reply_token

    try:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"Echo: {text}"))
    except LineBotApiError as e:
        # 处理发送消息时可能出现的错误
        print(f"Error: {e}")

# 注意：如果您使用 AWS Lambda，以下代码块不会被执行，因为入口点是 lambda_handler 函数
if __name__ == '__main__':
    app.run()



