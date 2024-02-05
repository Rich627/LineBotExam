# user_session.py
import boto3
from boto3.dynamodb.conditions import Key

class UserSessionManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('UserSessions')

    def get_or_create_session(self, user_id):
        response = self.table.get_item(Key={'userId': user_id})
        if 'Item' in response:
            return response['Item']
        else:
            self.table.put_item(Item={
                'userId': user_id,
                'currentQuestionIndex': 0,
                'correctAnswers': 0
            })
            return {'userId': user_id, 'currentQuestionIndex': 0, 'correctAnswers': 0}

    def update_session(self, user_id, current_question_index, correct_answers):
        self.table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET currentQuestionIndex = :val1, correctAnswers = :val2',
            ExpressionAttributeValues={
                ':val1': current_question_index,
                ':val2': correct_answers
            }
        )
