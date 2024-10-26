from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import json
from selenium.webdriver.support import expected_conditions as EC

# Define driver 
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Maximum cửa sổ khi bắt đầu chạy 
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
# chrome_options.add_argument("--headless")  # Chạy Chrome ở chế độ headless
# chrome_options.add_argument("--disable-gpu")  # Vô hiệu hóa GPU (đề xuất cho headless)
chrome_options.add_experimental_option('prefs', {"profile.managed_default_content_settings.images": 2})  # Cho phép không cần load hình ảnh
driver = webdriver.Chrome(options=chrome_options)  # Define driver with options 

def login_facebook(driver, email, password):
    driver.get('https://www.facebook.com')  # Gọi URL FB 
    time.sleep(3)  # Nghỉ 3s 

    email_input = driver.find_element(By.ID, 'email')  # Tìm thẻ có id= email 
    password_input = driver.find_element(By.ID, 'pass')  # Tìm thẻ có id= pass 
    email_input.send_keys(email)  # Nhập email
    password_input.send_keys(password)  # Nhập password 

    login_button = driver.find_element(By.NAME, 'login')  # Tìm thẻ có name= login 
    login_button.click()  # Tạo sự kiện click trên thẻ login 
    time.sleep(10)
    
login_facebook(driver, 'pqielts2023@gmail.com', 'vietnam12345@')  # Thay tài khoản, mật khẩu = tài khoản mật khẩu FB

def click_more_content(driver): 
    try: 
        ActionChains(driver).move_to_element(driver.find_element(By.XPATH, '//div[contains(text(), "Xem thêm")]')).click().perform()
        time.sleep(2)
    except Exception as e:
        print(f"Error clicking more content: {e}")

def crawl_time(driver, value_aria): 
    time_element = driver.find_element(By.XPATH, f'//span[@aria-labelledby="{value_aria}"]') 
    ActionChains(driver).move_to_element(time_element).perform()  # Thiết lập hover di chuột đến time để hiện thị ngày tháng năm thực tế
    time.sleep(1)
    
    return driver.find_element(By.XPATH, '//div[@role="tooltip"]').text

def crawl_infor_post_group(driver, html): 
    main_link = 'https://www.facebook.com'
    
    name_group = html.find('div', attrs={'dir': 'ltr'}).span.text
    link_group = main_link + html.find('div', attrs={'dir': 'ltr'}).a.get('href')
    
    user_post_name = html.find('div', attrs={'id': re.compile(':r*')}).span.text
    user_post_link = main_link + html.find('div', attrs={'id': re.compile(':r*')}).a.get('href')
    ariana_value = html.find('span', attrs={'aria-labelledby': True}).get('aria-labelledby')
    return name_group, link_group, user_post_name, user_post_link, crawl_time(driver, ariana_value)

def crawl_infor_post_page(driver, html):
    name_page = html.find('span', attrs={'dir': 'ltr'}).find('span').text
    link_page = html.find('span', attrs={'dir': 'ltr'}).a.get('href')
    
    ariana_value = html.find('span', attrs={'aria-labelledby': True}).get('aria-labelledby')
    return name_page, link_page, crawl_time(driver, ariana_value)

def crawl_post(html): 
    try: 
        return '\n'.join([i.text for i in html.find('div', attrs={'data-ad-preview': 'message'}).find_all('div', attrs={'dir': 'auto'})])
    except:
        return html.find('div', attrs={'dir': 'auto'}).text

# def click_recents_post(driver):
#     try:
#         recents_button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Recent posts"]'))
#         )
#         recents_button.click()
#         print("Clicked on Recent Posts tab.")
#     except Exception as e:
#         print(f"Error clicking on Recent Posts: {e}")


def scrape_facebook_posts(driver, name_file, search_query, num_posts):
    search_url = f'https://www.facebook.com/search/posts/?q={search_query}'
    driver.get(search_url)
    time.sleep(10)  # Thêm thời gian chờ để đảm bảo trang đã tải xong

    # Nhấn vào tab "Recent Posts"
    # click_recents_post(driver)  # Gọi hàm click_recents_post với driver

    f = open(f'{name_file}', 'w', encoding='utf-8')
    post_count = 0
    collected_posts = set()

    while post_count < num_posts:
        click_more_content(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        posts_container = soup.find('div', attrs={'role': 'feed'})
        if posts_container:
            posts = posts_container.find_all('div', attrs={'data-virtualized': 'false'})
        else:
            print("No feed found")
            break

        for post in posts:
            if post_count >= num_posts:
                break
            try:
                content = crawl_post(post)
                if content not in collected_posts:
                    collected_posts.add(content)
                    try:
                        name_group, link_group, user_post_name, user_post_link, time_post = crawl_infor_post_group(driver, post)
                    except:
                        user_name, user_link, time_post = crawl_infor_post_page(driver, post)

                    # Kiểm tra nếu time_post thỏa mãn điều kiện
                    time_format = "%A %d %B %Y at %H:%M"  # Định dạng thời gian
                    time_post_date = datetime.strptime(time_post, time_format)  # Chuyển đổi thành datetime

                    # Lọc chỉ những bài đăng có thời gian từ 1/10 đến 8/10
                    if time_post_date.year == 2024 and time_post_date.month == 10 and 1 <= time_post_date.day <= 8:
                        data_dumps = json.dumps({
                            'user_name': user_post_name,
                            'user_link': user_post_link,
                            'name_group': name_group,
                            'group_link': link_group,
                            'time_post': time_post,
                            'content': content
                        }, ensure_ascii=False)

                        f.write(data_dumps + '\n')
                        post_count += 1
                        print(f"Post: {post_count}: {content}")
            except Exception as e:
                print("Cannot get content:", str(e))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    f.close()

if __name__ == '__main__':
    scrape_facebook_posts(driver, 'viettel_scrape_new.jsonl', 'viettel', 2000)
