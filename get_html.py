from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from twocaptcha import TwoCaptcha
import time
import os

def get_captcha_solution(api_key, captcha_img_src):
    solver = TwoCaptcha(api_key)
    try:
        result = solver.solve_and_return_solution(captcha_img_src)
        if result['code']:
            print("Captcha solved: " + result['code'])
            return result['code']  # 获取验证码的解决方案
        else:
            print("Failed to solve captcha.")
            return None
    except Exception as e:
        print(f"Error solving captcha: {e}")
        return None

def download_page(driver, url, api_key):
    driver.get(url)
    time.sleep(5)  # 增加等待时间以确保页面完全加载

    # 检查是否存在验证码
    try:
        captcha_img_element = driver.find_element(By.CSS_SELECTOR, 'img.captcha')
        captcha_img_src = captcha_img_element.get_attribute('src')

        # 解决验证码
        captcha_solution = get_captcha_solution(api_key, captcha_img_src)
        if captcha_solution:
            captcha_input_element = driver.find_element(By.ID, 'id_captcha_1')
            captcha_input_element.send_keys(captcha_solution)

            submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

            time.sleep(3)  # 等待反馈结果

            # 再次检查是否仍然在验证码页面
            if driver.find_elements(By.CSS_SELECTOR, 'img.captcha'):
                print("Captcha not solved. Skipping page.")
                return None
    except NoSuchElementException:
        print("No captcha found. Proceeding to download page.")

    return driver.page_source if "Temporarily Restricted Page" not in driver.title else None

driver = webdriver.Chrome()
api_key = "6dfb03218fe6e90b13670b38b12cae48"

base_url = "https://www.examtopics.com/exams/amazon/aws-certified-developer-associate-dva-c02/view/"
res_directory = "res"

# 确保res目录存在
if not os.path.exists(res_directory):
    os.makedirs(res_directory)

# 爬取前3页
for page_number in range(1, 4):
    url = f"{base_url}{page_number}/"
    print(f"Processing {url}")
    html = download_page(driver, url, api_key)
    if html:
        filename = os.path.join(res_directory, f"page_{page_number}.html")
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(html)
        print(f"Downloaded and saved {filename}")
    else:
        print(f"Failed to download or page restricted: {page_number}")

driver.quit()



