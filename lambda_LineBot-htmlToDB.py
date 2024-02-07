import boto3
from bs4 import BeautifulSoup as bs
from urllib.parse import unquote_plus
import re

# Initialize the boto3 client and resource outside the handler for potential reuse
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
quiz_questions_table = dynamodb.Table('QuizQuestions')

def lambda_handler(event, context):
    for record in event['Records']:
        # Correctly retrieve the bucket name
        bucket_name = record['s3']['bucket']['name']
        # Decode the object key
        key = unquote_plus(record['s3']['object']['key'])

        # Get the content of the S3 object
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            html_content = response['Body'].read().decode('utf-8')
        except s3_client.exceptions.NoSuchKey:
            print(f"The specified key does not exist: {key}")
            continue

        # Parse the HTML content
        soup = bs(html_content, 'html.parser')

        # Extract questions from the HTML
        question_cards = soup.find_all("div", class_="card exam-question-card")
        for question_card in question_cards:
            # Extract the question number from the question title
            question_number = re.search(r"Question #(\d+)", question_card.find("div", class_="card-header").text)
            if question_number:
                question_id = int(question_number.group(1))
            else:
                continue  # If no question number is found, skip this question

            question = __get_question(question_card)
            answers = __get_answers(question_card)
            correct_answer = __get_correct_answer(question_card)
            options = {chr(65+i): answer for i, answer in enumerate(answers)}
            
            # Store the extracted information into DynamoDB
            response = quiz_questions_table.put_item(
                Item={
                    'QuestionID': question_id,  # Use the extracted question number as QuestionID
                    'Question': question,
                    'Options': options,
                    'CorrectAnswer': correct_answer
                }
            )

            print(f"Successfully processed question number {question_id}.")

def __clean_string(string):
    """Clean up the string"""
    string = re.sub(r"\s+", " ", string)  # Replace multiple spaces with a single space
    return string.strip()

def __get_question(question_card):
    """Extract the question from the question card"""
    question = question_card.find("p", class_="card-text").text
    return __clean_string(question)

def __get_answers(question_card):
    """Extract all answers from the question card"""
    answers = [li.text for li in question_card.find_all("li", class_="multi-choice-item")]
    return [__clean_string(answer) for answer in answers]

def __get_correct_answer(question_card):
    """Extract the correct answer from the question card"""
    correct_answer = question_card.find("span", class_="correct-answer").text
    return __clean_string(correct_answer)
