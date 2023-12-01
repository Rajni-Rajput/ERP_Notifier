from selenium import webdriver
from selenium.webdriver.chrome.service import Service as BraveService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager
#from webdriver_manager.core.utils import ChromeType

import time
import sys
import datetime as dt
import yaml

from dateutil.parser import parse
from plyer import notification
from bs4 import BeautifulSoup as bS

# import cProfile

def login_user(user_id, pass_word):
    options = Options()
    options.add_argument("--headless")
    #options.add_experimental_option("detach", True)

    driver_start = webdriver.Chrome(service=webdriver.ChromeService(), options=options)

    driver_start.get("https://mrei.icloudems.com/corecampus/index.php")

    uname_field = driver_start.find_element(By.ID, "useriid")
    pass_field = driver_start.find_element(By.ID, "actlpass")

    login_btn = driver_start.find_element(By.ID, "psslogin")

    uname_field.clear()
    pass_field.clear()

    uname_field.send_keys(user_id)
    pass_field.send_keys(pass_word)

    login_btn.click()

    driver_start.implicitly_wait(10.0)
    home_page = driver_start.find_elements("xpath", "//div[contains(@class, 'col-md-2 col-sm-3 text-center')][.//a[contains(@href, 'assignments/') or contains(@href, 'attendance/')]]//a")
    # try:
    #     get_assignment_page[0].click()
    # except IndexError:
    #     login_user(user_id, pass_word)

    # assignments_page = driver_start.page_source
    # driver_start.quit()

    return [driver_start, home_page]


def is_valid_date(due_date_p):
    try:
        date_str = parse(due_date_p, dayfirst = True)
        return True, date_str.date()

    except ValueError:
        return False, 1 

def get_assignments(driver, link):
    link.click()
    driver.implicitly_wait(10.0)
    assignment = driver.page_source
    # driver.quit()
    assignment_soup = bS(assignment, 'lxml')
    # print(assignment_soup)
    table = assignment_soup.find('table')
    if table == None:
        notification.notify(
            title = "ERP assignment notifier",
            message = "An Error has occured. Please reopen the application",
            timeout = 3,
            app_name = "ERP"
        )
        sys.exit()

    s_no = [value.text.strip() for value in table.find_all('td')]
    # print(s_no)
    if s_no == None:
        notification.notify(
            title = "ERP assignment notifier",
            message = "There are no assignments",
            timeout = 3,
            app_name = "ERP"
        )
        
    table_sNo_length = len([s_no[number] for number in range(0, len(s_no), 10)])
    # print(table_sNo_length)
    s_no.clear()

    table_val_submitted = (submit for submit in iter(table.find_all('i')) if str(submit) in ('<i class="far fa-times-circle text-danger"></i>', '<i class="fas fa-check-circle text-success"></i>'))
    # print(table_val_submitted)

    assign_list = [val.text.strip() for val in table.find_all('font') if val.text.strip() != '']
    # print(assign_list)

    pending = sum(1 for assignments in assign_list if (valid_date_str := is_valid_date(assignments))[0] and not (dt.date.today() >= valid_date_str[1]) and str(next(table_val_submitted)) == '<i class="far fa-times-circle text-danger"></i>')

    with open("config.yaml", "r+") as f:
        data = yaml.safe_load(f)
        if (table_sNo_length > data['total_assignments']):
            data['total_assignments'] = table_sNo_length
            yaml.dump(data, f)
            notification.notify(
                title = "ERP assignment notifier",
                message = f"You have {pending} pending assignment(s) and {table_sNo_length - int(data['total_assignments'])} new assignment(s).",
                timeout = 3,
                app_name = "ERP"
                )
        else:
            notification.notify(
                title = "ERP assignment notifier",
                message = f"You have {pending} pending assignment(s).",
                timeout = 3,
                app_name = "ERP"
            )

def get_attendance(driver, link):
    link.click()
    driver.implicitly_wait(10.0)
    attendance = driver.page_source
    # driver.quit()
    attendance_soup = bS(attendance, 'lxml')
    table = attendance_soup.find('table')
    if table == None:
        notification.notify(
            title = "ERP assignment notifier",
            message = "An Error has occured. Please reopen the application",
            timeout = 3,
            app_name = "ERP"
        )
        sys.exit()
    
    attendance_dict = {}
    for row in table.find_all('tr')[1:len(table.find_all('tr')) - 1]:
        columns = row.find_all('td')
        if float(columns[5].text.strip()) < 75.0:
            attendance_dict[columns[1].text.strip()] = columns[5].text.strip()
    
    low_att = ', '.join(f'{subject}:{value}' for subject, value in attendance_dict.items())
    if low_att:
        notification.notify(
                title = "ERP attendance notifier",
                message = f"You have low attendance in {low_att}",
                timeout = 3,
                app_name = "ERP"
            )
    else:
        notification.notify(
                title = "ERP assignment notifier",
                message = f"You do not have low attendance in any subject",
                timeout = 3,
                app_name = "ERP"
            )
#Main Code
try:
    interval = 24*60*60

    while True:
        with open("config.yaml", "r") as log:
            cred = yaml.safe_load(log)
            homepage = login_user(cred['username'], cred['password'])
            home_driver = homepage[0]
            if homepage[1] != []:
                inp = int(input("Assignment or Attendance(1/2):"))
                if inp == 1:
                    get_assignments(homepage[0], homepage[1][0])
                elif inp == 2:
                    get_attendance(homepage[0], homepage[1][1])
                else:
                    raise Exception("Invalid choice")
            else:
                notification.notify(
                        title = "ERP assignment notifier",
                        message = "Unable to reach \"mrei.icloudems.com\" retrying",
                        timeout = 2,
                        app_name = "ERP"
                )
                continue
            # cProfile.run("get_assignments(assignment_page)", sort="cumtime")
            # sys.exit()
            homepage[0].quit()
        time.sleep(interval)

except FileNotFoundError:
    notification.notify(
        title = "ERP assignment notifier",
        message = "Username/Password file not found.",
        timeout = 3,
        app_name = "ERP"
    )
    sys.exit()
