# quiz.py
from io import TextIOWrapper
from _classes import CardList, os, re
import random
from datetime import datetime 
import textwrap

class Quiz:
    def __init__(self, resources_dir=None) -> None:
        self.__cardlist = CardList(resources_dir)
        self.__log_dirname = "wrong_answers"
        self.__init_questions_per_quiz()
        # self.__create_wrong_answers_directory()  
        self.quiz_cards = self.__generate_quiz()

    def __init_questions_per_quiz(self):
        """
        Initialize the variable that shows how many questions should be shown in a quiz run
        """
        self.__questions_per_quiz = len(self.__cardlist.cards_list)

    def __generate_quiz(self) -> list:
        """
            Generate a random list of card objects that are limited by the size of how
            many questions the player wants to have
        """
        random.shuffle(self.__cardlist.cards_list)
        return self.__cardlist.cards_list[:self.__questions_per_quiz]

    # def __create_wrong_answers_directory(self):
    #     try:
    #         os.mkdir(self.__log_dirname)
    #     except:
    #         print("Wrong answers directory already exists. Continuing..")
            
    def __init_answers_file(self) -> TextIOWrapper:
        """
            Initialize the filename with the current datetime, while omitting spaces and colon
        """
        filename = re.sub(" ", "_", str(datetime.now())).split(".")[0]  # remove the miliseconds as they were delimited by '.'
        filename = re.sub(":", "-", filename)  # remove ':' as they are a special char on Windows.. 
        filename += ".txt"
        filename = os.path.join(self.__log_dirname, filename)
        wrong_answers_file = open(filename, "w")  # file where the wrong answers will be written to

        return wrong_answers_file
    
    def __write_to_file(self, wrong_answers_file, card, your_answer):
        
        wrapper = textwrap.TextWrapper()  # wrap text so it looks better

        wrong_answers_file.write(card.question_number + " " + wrapper.fill(text= card.question) + "\n")
        wrong_answers_file.write("-" * 40 + "\n")
        for ans in card.answers:
            try:
                # ans = str(ans.encode('utf-8'))  # some answers give a UnicodeEncodeError: 'charmap' codec can't encode character '\u05d2' in position 192: character maps to <undefined>
                wrong_answers_file.write(wrapper.fill(text= ans) + "\n")  # one answer had a weird encoding
            except:
                wrong_answers_file.write(str(ans) + "\n")

        wrong_answers_file.write("Your answer: " + your_answer.upper() + "\n")
        wrong_answers_file.write("Correct answer: " + card.correct_answer + "\n")
        wrong_answers_file.write("-" * 40 + "\n\n")

    def start_quiz(self, user_session):
        self.quiz_cards = self.__generate_quiz()
        if not self.quiz_cards:
            return "Can't start the quiz. No questions available."
        first_question = self.quiz_cards[user_session.current_question_index]
        question_text = f"{first_question.question}\n\n"  
        options_text = "\n".join(first_question.answers)
        return f"{question_text}{options_text}"

    def answer_question(self, user_session, user_answer):
        card = self.quiz_cards[user_session.current_question_index]
        correct = user_answer.strip().upper() == card.correct_answer.strip().upper()
        user_session.correct_answers += int(correct)
        result_string = "Correct!" if correct else f"Wrong, the correct answer is {card.correct_answer}.\n"

        user_session.current_question_index += 1

        if user_session.current_question_index < len(self.quiz_cards):
            next_card = self.quiz_cards[user_session.current_question_index]
            question_text = f"{next_card.question}\n\n" 
            options_text = "\n".join(next_card.answers)
            return f"{result_string}\n{question_text}{options_text}"
        else:
            return f"{result_string}\nYour score is {user_session.correct_answers}/{len(self.quiz_cards)}."


