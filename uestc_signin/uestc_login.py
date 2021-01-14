# coding=utf-8
#
# Copyright (c) 2020 The UESTC-Signin Authors. All rights reserved.
# Use of this source code is governed by a MIT-style license that can be
# found in the LICENSE file. See the AUTHORS file for names of contributors.
#
# Authors: ehds(ds.he@foxmail.com)

import logging
import time
import json
import os
import base64
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import requests
from .baidu import baidu_ocr
from .captcha import CalcMoveOffset

logger = logging.getLogger(__name__)


class page_load_state(object):
    """An expectation for the page to be located is completed or loading."""

    def __init__(self, state):
        self._state = state

    def __call__(self, driver):
        return driver.execute_script('return document.readyState') == self._state


class loaded_weu_cookie(object):
    """An expectation for the _WEU cookie item loaded"""

    def __init__(self):
        pass

    def __call__(self, driver):
        if page_load_state('complete')(driver):
            current_cookies = {}
            for elem in driver.get_cookies():
                current_cookies[elem['name']] = elem['value']
            return "_WEU" in current_cookies and len(current_cookies["_WEU"]) >= 152
        return False


class Login(object):
    def __init__(self, user, passwd, driver_name="firefox"):
        self.user = str(user)
        self.passwd = str(passwd)
        self.driver_name = driver_name
        self.driver = None
        self.timeout = 10  # second

    def init_driver(self):
        if (self.driver_name == "firefox"):
            # set options
            options = webdriver.FirefoxOptions()
            # without GUI window
            options.add_argument('--headless')
            cap = DesiredCapabilities().FIREFOX
            cap["marionette"] = True
            self.driver = webdriver.Firefox(
                options=options, capabilities=cap, executable_path='./driver/geckodriver')
            self.driver.implicitly_wait(self.timeout)

    def release_driver(self):
        if self.driver != None:
            self.driver.quit()

    def login(self) -> bool:
        if self.check_cookies_valid():
            return True

        if self.driver == None:
            self.init_driver()

        driver = self.driver
        driver.implicitly_wait(10)

        driver.get(
            "https://mapp.uestc.edu.cn/site/uestcService/index?ticket=ST-150915-1u1eImAqIyPsxrugzxlf1590930369193-vuau-cas")
        # saving the login page
        time.sleep(5)
        logger.debug('finding login element')
        # # find usename and passwd element
        user = driver.find_element_by_id("username")
        passwd = driver.find_element_by_id("password")

        # login uestc
        login_btn = driver.find_element_by_class_name("auth_login_btn")

        user.send_keys(self.user)
        passwd.send_keys(self.passwd)

        logger.debug('clicking login button')
        login_btn.click()
        time.sleep(2)

        # complete captcha (move slider bar)
        # mabye fail we can try many times
        for _ in range(20):
            captcha_img_ele = driver.find_element_by_xpath(
                '/html/body/div[1]/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div/canvas[1]')
            captcha_base64 = driver.execute_script(
                "return arguments[0].toDataURL('image/png').substring(21);", captcha_img_ele)
            width = driver.execute_script(
                "return arguments[0].width", captcha_img_ele)

            template_img_ele = driver.find_element_by_xpath(
                '/html/body/div[1]/div[2]/div[2]/div/div[1]/div/div/div/div[2]/div/canvas[2]')
            template_base64 = driver.execute_script(
                "return arguments[0].toDataURL('image/png').substring(21);", template_img_ele)

            # decode
            origin_png = base64.b64decode(captcha_base64)
            with open("captcha.png", 'wb') as f:
                f.write(origin_png)

            template_png = base64.b64decode(template_base64)
            with open("template.png", 'wb') as f:
                f.write(template_png)

            offset = CalcMoveOffset('./captcha.png', 'template.png', width)
            source = driver.find_element_by_class_name('slider')
            actions = ActionChains(
                driver).drag_and_drop_by_offset(source, offset, 0)
            actions.perform()
            # wating redirect if succes
            time.sleep(2)
            # vertify if login success
            if "authserver" not in driver.current_url:
                break
        # not need captcha anymore
        else:
            self.release_driver()
            logger.error("log in failed,maybe username of password is wrong")
            return False

        # enter app for getting login cookies
        driver.get(
            "http://eportal.uestc.edu.cn/qljfwapp/sys/lwReportEpidemicStu/*default/index.do#/dailyReport")

        try:
            # wating until we get _WEU cookie item for task
            WebDriverWait(driver, 15).until(
                loaded_weu_cookie()
            )
        except Exception as e:
            logger.error("Loding cookie error {}".format(e))
            return False
        finally:
            Login.save_cookies(driver.get_cookies())
            self.release_driver()
        # everythin is ok, login is ok
        return True

    @classmethod
    def save_cookies(cls, driver_cookies):
        cookies = {}
        for elem in driver_cookies:
            cookies[elem['name']] = elem['value']

        cookie_json = json.dumps(cookies, indent=4)
        with open("./data/cookies.json", "w") as f:
            f.write(cookie_json)

    @classmethod
    def load_cookies(cls):
        if not os.path.exists(os.path.join("./data/cookies.json")):
            return {}
        else:
            with open("./data/cookies.json", "r") as f:
                return json.load(f)

    def check_cookies_valid(self):
        cookies = Login.load_cookies()
        lastest_daily_report_url = "http://eportal.uestc.edu.cn/jkdkapp/sys/lwReportEpidemicStu/mobile/dailyReport/getLatestDailyReportData.do"
        post_data = {
            "pageNum": 1,
            "pageSize": 10,
            "USER_ID": self.user
        }
        headers = {
            'Origin': 'http://eportal.uestc.edu.cn',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0',
        }
        last_daily_data = requests.post(
            lastest_daily_report_url, data=post_data, headers=headers, cookies=cookies).content
        try:
            _ = json.loads(last_daily_data)
            return True
        except Exception as e:
            logger.debug(f"Cookies is unvalid {e}")
        return False

def ReLogin(config):
    if config.user is None or config.password is None:
        print("you need to set username and passwd")
        return False

    login = Login(config.user, config.password)
    # check if cookies is valid
    try:
        login_status = login.login()
        return login_status
    except Exception as e:
        logger.error(f"Login failed {e}")
        login.release_driver()
        return False
