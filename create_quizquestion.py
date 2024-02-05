import boto3

# 初始化 DynamoDB 客户端
dynamodb = boto3.resource('dynamodb')

# 选择表
table = dynamodb.Table('quizquestion')

# 添加项
response = table.put_item(
   Item={
        'question_id': 'q1',
        'question': 'What is the capital of France?',
        'answer': ['Paris', 'Rome', 'Madrid', 'Berlin'],
        'correct_answer': 'Paris'
    }
)
