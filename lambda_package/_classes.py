# _calsses.py
from bs4 import BeautifulSoup as bs
import os 
import re 
import boto3
from boto3.dynamodb.conditions import Key

class Card:
    """ 
        Represnts a structure which holds all a question with answers and a correct answer

        ! To not be confused with a Page which would hold 4 Cards !
    """
    def __init__(self, _question: str, _answers: list, _correct_answer: str, _question_number: str) -> None:
        self.question = _question
        self.answers = _answers
        self.correct_answer = _correct_answer
        self.question_number = _question_number
    

    def print_card(self):
        print("="*20)
        print("Question ", self.question_number, ": ")
        print(self.question)
        print("="*20)
        print("~"*20)
        print("Answers:")
        print(self.answers)
        print("~"*20)
        print(self.correct_answer)


class CardList:
    def __init__(self, bucket_name) -> None:
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.__page_soup_list = self.__init_soup(self.__get_list_of_html())
        self.cards_list = []

        for page_soup in self.__page_soup_list:
            cards_on_page = self.__get_all_cards(page_soup)
            for card in cards_on_page:
                self.cards_list.append(card)

    def __get_list_of_html(self) -> list:
        """Get HTML file names from S3 bucket"""
        objects = self.s3_client.list_objects_v2(Bucket=self.bucket_name)['Contents']
        html_files = [obj['Key'] for obj in objects if obj['Key'].endswith('.html')]
        return html_files

    def __init_soup(self, html_list: list):
        """Creates a list of BeautifulSoup objects for each HTML file"""
        soup_list = []
        for html_file in html_list:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=html_file)
            soup = bs(obj['Body'].read().decode('utf-8'), "html.parser")
            soup_list.append(soup)
        return soup_list

    def __get_all_cards(self):
        """ 
        從DynamoDB表中讀取所有卡片數據。
        """
        response = self.table.scan()
        cards = []
        for item in response['Items']:
            question = item['question']
            answers = item['answers']
            correct_answer = item['correct_answer']
            question_number = item['question_number']
            cards.append(Card(question, answers, correct_answer, question_number))
        return cards


    def __clean_string(self, string: str) -> str:
        """ 
            Removes \n and whitespace in front and back of the string
        """
        string = re.sub(r"^[\n\s]+", "", string)
        string = re.sub(r"[\n\s]+$", "", string)  # fixed: trailing spaces are now removed
        string = re.sub(r"\n", " ", string)  # get rid of newlines in string
        string = re.sub(r"\s{2,}", " ", string)  # substitute more than 2 spaces in only 1
        string = string.rstrip()  # remove trailing space if necessary
        # get rid of Most Voted from the back of the answers
        _ = string.split(" ")
        if len(_) >= 2:
            if " ".join(_[-2:]).lower() == "most voted":  # if last 2 words are 'most voted'
                string = " ".join(_[:-2])  # get rid of them

        # get rid of some weird non-ascii chars that break the app 
        string = string.encode("ascii",errors="ignore").decode()

        return string


    def __get_question_number(self, card_body) -> str:
        """ 
            Get the question nubmer for easier debuggind purposes.
            
            When getting the div with class 'card-header text-white bg-primary',
            a string of type 'Question <number> Topic 1' is returned. We
            split to only get the number
        """
        return self.__clean_string(card_body.find("div", attrs={'class': "card-header text-white bg-primary"}).text).split(" ")[1]

        
    def __get_question(self, card_body) -> str:
        """ 
            Returns the question available in the body of this card
        """
        return self.__clean_string(card_body.find("p", attrs={'class': "card-text"}).text)


    def __get_answers(self, card_body) -> list:
        """ 
            Returns the four answers available in the body of this card
        """

        set_of_answers = card_body.find_all("li", attrs={'class': "multi-choice-item"})  # answers on a card
        set_of_answers = [self.__clean_string(_.text) for _ in set_of_answers]  # get rid of tags

        return set_of_answers


    def __get_correct_answer(self, card_body) -> str:
        """ 
        Returns the correct answer from a card.

        As the "correct answer" stated by ExamTopics is usually wrong,
        the metric that is used here is to get the most popular (first) 
        answer from the progress bar (Community vote distribution bar)

        It appears that some questions (ex. #40) do not show the progress
        bar after clicking reveal, but somehow the tag is still there,
        even though I cannot see it.

        ! WARN: 
        Some (many) questions do not have a most voted answer as the
        correct answer is actually the one selected by ExamTopics.
        As such, to mitigate the issue, we use the fact that every Card
        has tag <p class="card-text question-answer bg-light white-text">.
        If it doesn't have "vote-bar progress-bar bg-primary", we'll
        default to the primary answer.
        """

        cabody = card_body.find("p", attrs={'class': "card-text question-answer bg-light white-text"})  # correct answers body

        comm_correct_answer = cabody.find("div", attrs={'class': "vote-bar progress-bar bg-primary"})  # the bar with community answer
        
        # in the cases where the community agrees with ExamTopics, there is no community voting bar
        if comm_correct_answer != None:  
            correct_answer = comm_correct_answer.text.split(" ")[0]  # vote-bar progress-bar bg-primary
        else:
            correct_answer = cabody.find("span",attrs={'class': "correct-answer"}).text

        return correct_answer

    def get_cards(self) -> list:
        """ 
        返回卡片列表
        """
        return self.cards_list