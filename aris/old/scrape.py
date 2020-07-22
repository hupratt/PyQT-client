from selenium import webdriver
from bs4 import BeautifulSoup
import time, os,pickle
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver import FirefoxProfile, Firefox
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys


def launch_first_firefox(url):
    profile = FirefoxProfile()
    cap = DesiredCapabilities().FIREFOX
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', os.getcwd())
    profile.set_preference("browser.helperApps.neverAsk.openFile","application/xls")
    binary = FirefoxBinary('K://firefox.exe')
    driver = Firefox(firefox_profile=profile, firefox_binary=binary, capabilities=cap, executable_path = "K://geckodriver.exe")
    session_id = driver.session_id
    url_exec = driver.command_executor._url 
    driver.get(url)
    return session_id, url_exec


def grab_urls(driver, liste):
    soup = BeautifulSoup(driver.page_source,'lxml')
    #for each "cpn-advancedSearch-search-result-name"
    #"copy data-item-id"
    search_results = soup.find_all('div',class_='cpn-advancedSearch-search-result-name')
    list_of_processes_item_url = ["http://" + search_result['data-item-id'] for search_result in search_results]
    liste.extend(list_of_processes_item_url)
    return liste

def next_page(driver, liste):
    for i in range(2,11):
        # aria-label="Page 2"
        # "gwt-Anchor cpn-extendedGlobalSearch-pagination cpn-extendedGlobalSearch-pageLink"
        search = "//a[@aria-label='Page "+ str(i) +"']"
        next_page = driver.find_element_by_xpath(search)
        next_page.click()
        time.sleep(5)
        liste = grab_urls(driver, liste)
    return liste

def connect_existing_browser(session_id, url):
#    session_id = "0adf3d60-da76-4a2b-9f8f-87b3e27e009d"
#    url = "http://127.0.0.1:57225/hub"
    driver = webdriver.Remote(command_executor=url)
    driver.session_id = session_id
    return driver



def save(liste):
    with open("liste.txt", 'wb') as f:
        pickle.dump(liste, f)

def load():
    with open("liste.txt", 'rb') as f:
        data = pickle.load(f)
        f.close()
        return data

#def main():
session_id, url = launch_first_firefox("http://")
input("Press continue to resume")
driver = connect_existing_browser(session_id, url)
#driver = connect_existing_browser("2045e378-9847-4c2f-a492-55305359f323", "http://127.0.0.1:65129/hub")
liste = grab_urls(driver, list())
liste = next_page(driver, liste)
print(f"{len(liste)} urls were grabbed so far")
save(liste)
liste = load()

def grab_report(liste, driver):
    # icon iconlib_show_report_result_16
    for url in liste:
        driver.get(url)
        time.sleep(8)
        report_icon = driver.find_element_by_xpath("//span[@class='icon iconlib_show_report_result_16']")
        report_icon.click()
        #gwt-uid-1053
        time.sleep(1)
        report_name = driver.find_element_by_xpath("//input[@aria-label='Select report script to run']")
        report_name.click()
        time.sleep(1)
        report_name.send_keys(100 * Keys.BACKSPACE)
        time.sleep(1)
        
        report_name.send_keys('Output model information')
        report_name.send_keys(Keys.ENTER)
        #gwt-uid-1051
        time.sleep(1)
        report_format = driver.find_element_by_xpath("//input[@aria-label='Select report format']")
        report_format.click()
        time.sleep(1)
        report_format = driver.find_element_by_xpath("//a[@title='Output XLS']")
        time.sleep(1)
        report_format.click()
        start = driver.find_element_by_xpath("//a[@aria-label='Start']")
        start.click()
        time.sleep(5)
        start_dl = driver.find_element_by_xpath("//a[@aria-label='Download result']")
        start_dl.click()
        time.sleep(100)
        
grab_report(liste, driver)

#if __name__ == "__main__":
#    main()
