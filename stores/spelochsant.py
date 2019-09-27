from requests_html import HTMLSession
session = HTMLSession()
r = session.get('https://www.spelochsant.se/kategori/sallskapsspel/bradspel:375')


import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Firefox
driver = webdriver.Firefox(options=options)
driver.get(WEBHALLENURL)
driver.implicitly_wait(3)


driver.find_elements_by_css_selector('div#product_list_table_pager.table_pager div.page_button')


from selenium.webdriver.common.action_chains import ActionChains
actions = ActionChains(driver)
actions.move_to_element(bb).click().perform()

mip = buts[2]

mip.text
'3'

mip.click()


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# WOrks !!!!
element = driver.find_element_by_css_selector('div.cc_banner.cc_container.cc_container--open')
driver.execute_script("arguments[0].style.visibility='hidden'", element)

