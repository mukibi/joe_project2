from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

driver = webdriver.PhantomJS(service_args=["--load-images=no"])	

driver.get("http://www.google.co.uk/");

page = driver.find_element_by_tag_name("body").text

print(page)


