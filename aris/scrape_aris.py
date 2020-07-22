from selenium import webdriver
from PyQt5 import QtCore
from bs4 import BeautifulSoup
import time
import os
import pickle
import logging
import pandas as pd
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver import FirefoxProfile, Firefox
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    ElementNotVisibleException,
)
from pandas import ExcelWriter, DataFrame
from typing import List, Union
from my_jira_app.utils import MyLogger, Loader, search_import_file, path_leaf


class Scrape_ARIS(MyLogger, Loader, QtCore.QRunnable):
    """
    Crawl ARIS, download all reports, store them in the "ARIS/download"
    folder and log the ARIS url, the absolute path and the report name
    in the mapping file. This mapping file is the interface record
    between a JIRA key and a ARIS url. This is a 1 to 1 relationship
    Create_tcs.py will populate the mapping file with the JIRA_key
    created in the Create_tcs.py script
    """

    def __init__(self, progressbar=None, statusBar=None) -> None:
        QtCore.QRunnable.__init__(self)
        self.progressbar = progressbar
        self.statusbar = statusBar
        self.parent = os.path.dirname(os.getcwd())
        self.yml = self.load_yml("generated_config_aris.yml")
        self.firefox_binary_path = self.yml["FirefoxBinary"]  # noqa: E501
        self.geckodriver_binary = self.yml["Geckodriver_binary"]
        self.process_url = self.yml["process_url"]
        self.search_url = self.yml["search_url"]
        # Namespace for the logger
        self.script_name = path_leaf(__file__)
        self.pickle_file = self.yml["pickle_file"]
        self.download_folder = self.yml["download_folder"]
        self.temp_folder = self.yml["temp_folder"]
        self.mapping = self.yml["mapping_file_name"]
        self.log_name = self.yml["log_name"]
        self.master = self.yml["master"]
        self.apps = self.yml["apps"]
        self.delete_all_xls = self.yml["delete_all_xls_files_from_temp_and_download"]
        self.delete_mapping_file = self.yml["delete_mapping_file"]
        self.skip_url_retrieval = self.yml["skip_url_retrieval"]
        self.clear_everything_scape = self.yml["would_like_to_clear_everything_scrape"]
        self.delete_pickle = self.yml["delete_pickle"]

        super().__init__(log_name=self.log_name, name=self.script_name)

    def handle_QMessageBox_upstream_requests(self):
        if self.clear_everything_scape:
            self.run_delete_mapping_file()
            self.run_delete_all_xls()
            self.run_delete_pickle_file()
        if self.delete_mapping_file:
            self.run_delete_mapping_file()
        if self.delete_all_xls:
            self.run_delete_all_xls()
        if self.delete_pickle:
            self.run_delete_pickle_file()

    def run_delete_pickle_file(self):
        pickle_file = os.path.join(self.parent, self.apps, self.pickle_file)
        if os.path.isfile(pickle_file):
            os.remove(pickle_file)
            logging.getLogger(self.script_name).info(
                f"{self.pickle_file} was deleted")
        else:
            logging.getLogger(self.script_name).info(
                f"tried to delete {self.pickle_file} but could not be found")

    def run_delete_mapping_file(self):
        map_dir = os.path.join(self.parent, self.master, self.mapping)
        if os.path.isfile(map_dir):
            os.remove(map_dir)
            logging.getLogger(self.script_name).info(
                f"{self.mapping} was deleted")
        else:
            logging.getLogger(self.script_name).info(
                f"tried to delete {self.mapping} but could not be found")

    def run_delete_all_xls(self):
        xls_dir = os.path.join(self.parent, self.master, self.download_folder)
        if os.path.isdir(xls_dir):
            xls = search_import_file(".xls", where=xls_dir)
            list(map(lambda x: os.remove(x), xls))
            if len(xls) == 0:
                logging.getLogger(self.script_name).info(
                    "tried to delete the xls files but they could not be found")
            else:
                logging.getLogger(self.script_name).info(
                    f"{len(xls)} xls files were deleted")

    def launch_firefox(self):
        """
        Launch the browser client that will be controlled
        by the geckodriver called "driver" here
        """
        cap = DesiredCapabilities().FIREFOX
        cap["marionette"] = False

        profile = FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference(
            "browser.download.manager.showWhenStarting", False)
        profile.set_preference(
            "browser.download.dir",
            os.path.join(self.parent, self.master, self.temp_folder),
        )
        profile.set_preference(
            "browser.download.manager.alertOnEXEOpen", False)
        profile.set_preference("browser.download.manager.closeWhenDone", False)
        profile.set_preference(
            "browser.download.manager.focusWhenStarting", False)
        profile.set_preference(
            "browser.helperApps.neverAsk.saveToDisk", "application/msexcel"
        )

        binary = FirefoxBinary(os.path.join(
            self.parent, self.apps, self.firefox_binary_path))
        driver = Firefox(
            firefox_profile=profile,
            firefox_binary=binary,
            capabilities=cap,
            executable_path=os.path.join(
                self.parent, self.apps, self.geckodriver_binary)
        )
        session_id = driver.session_id
        localhost = driver.command_executor._url
        driver.get(self.search_url)

        return driver, session_id, localhost

    def grab_urls(self, driver, liste: list) -> list:
        """
        Grab urls from the ARIS built in search browser
        for each "cpn-advancedSearch-search-result-name"
        copy "data-item-id"
        """
        soup = BeautifulSoup(driver.page_source, "lxml")
        search_results = soup.find_all(
            "div", class_="cpn-advancedSearch-search-result-name"
        )
        list_of_processes_item_url = [
            self.process_url + search_result["data-item-id"]
            for search_result in search_results
            if search_result["data-item-id"][:9] == "c.process"
        ]
        liste.extend(list_of_processes_item_url)
        self.statusbar.showMessage(
            f"Step 1/2: Retrieved {len(liste)} urls so far")
        return liste

    def next_page(self, driver, liste: list) -> list:
        """
        Find the pagination button and visit the next page
        """
        try:
            for i in range(2, 1000):
                """
                aria-label="Page 2"
                "gwt-Anchor
                cpn-extendedGlobalSearch-pagination
                cpn-extendedGlobalSearch-pageLink"
                """
                search = "//a[@aria-label='Page " + str(i) + "']"
                next_page = driver.find_element_by_xpath(search)
                next_page.click()
                time.sleep(5)
                liste = self.grab_urls(driver, liste)
        except NoSuchElementException:
            pass
        return liste

    @staticmethod
    def connect_existing_browser(session_id: str, url: str):
        """
        Unused but might be useful function for future implementations
        session_id = "0adf3d60-da76-4a2b-9f8f-87b3e27e009d"
        url = "http://127.0.0.1:57225/hub"
        """
        driver = webdriver.Remote(command_executor=url)
        driver.session_id = session_id
        return driver

    def save_pickle(self, liste: list) -> None:
        """
        Utility function so that i can separate the first step of the script
        which consists of scrapping urls from the second step of the script
        which consists of visiting the scrapped urls in step 1
        """
        logging.getLogger(self.script_name).info(
            f"{len(liste)} urls were saved on {self.pickle_file}"
        )
        with open(self.pickle_file, "wb") as f:
            pickle.dump(liste, f)

    def load_pickle(self) -> Union[List[str], None]:
        """
        Utility function so that i can separate the first step of the script
        which consists of scrapping urlsfrom the second step of the script
        which consists of visiting the scrapped urls in step 1
        """
        with open(self.pickle_file, "rb") as f:
            data = pickle.load(f)
            logging.getLogger(self.script_name).info(
                f"{len(data)} urls were loaded from {self.pickle_file}"
            )
            if isinstance(data, list):
                return data
            return None

    def rename(self, filename: str) -> None:
        """
        Visit the temp file, rename the file with the correct name and move it
        to the self.download_folder
        """
        path_where_file_to_rename = os.path.join(
            self.parent, self.master, self.temp_folder
        )
        found = search_import_file(
            where=path_where_file_to_rename, extension="xls")
        if len(found) > 1:
            raise ValueError(
                f"Too many temp files in the {self.temp_folder} folder")
        try:
            file_to_rename = found[0]
            abs_path = os.path.join(
                self.parent, self.master, self.download_folder, filename
            )
            os.rename(file_to_rename, abs_path)
        except IndexError:
            time.sleep(10)

    @staticmethod
    def sanitize(string_input: str) -> str:
        """
        Remove unauthorized chars that might prevent us from creating a file
        """
        import string

        valid_chars = "_ %s%s" % (string.ascii_letters, string.digits)
        return "".join(c for c in string_input if c in valid_chars)

    def load_mapping_file(self):
        """
        Load the mapping file, if the file does not exist create it,
        the mapping file is the main output of this module
        """
        path_to_mapping = os.path.join(self.parent, self.master, self.mapping)
        if not os.path.exists(path_to_mapping):
            mapping_file = DataFrame(
                columns=["Process_filename", "JIRA_key", "Abs_path", "Tree"]
            )
        else:
            mapping_file = pd.read_excel(path_to_mapping, sheet_name="mapping")

        return mapping_file

    def grab_exi_file_path(self, filename: str) -> str:
        """
        Grab the file path of the previously renamed process
        """
        time.sleep(2)
        abs_path = os.path.join(
            self.parent, self.master, self.download_folder, filename
        )
        found = os.path.isfile(abs_path)
        if found is False:
            input(
                """
                glitch with ARIS
                click on the download link manually
                and check whether the file was downloaded to the temp folder
                """
            )
            self.rename(filename)
        return abs_path

    @staticmethod
    def find_sub_group(tree_span: list) -> str:
        tree_span_found = ""
        for span in tree_span:
            if (
                len(span) > 0
                and span[0].isalpha()
                and span[0].isupper()
                and span[1] == "."
            ):
                tree_span_found = span.replace("/", "")
        return tree_span_found

    def update_progress_bar(self, currentPercentage):
        self.statusbar.showMessage(
            f"Step 2/2: Downloading reports: {int(currentPercentage)} %")
        QtCore.QMetaObject.invokeMethod(self.progressbar, "setValue",
                                        QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(
                                            int, currentPercentage))

    def grab_report(self, liste: list, driver) -> DataFrame:
        """
        Scrape the process page fopr the xls page and other info like
        the active tree where the process lives
        """
        mapping_file = DataFrame(
            columns=["Process_filename", "JIRA_key", "Abs_path", "Tree"]
        )
        for i, url in enumerate(liste):

            """
            Since this process takes ages
            we'll start saving the mapping_file dataframe
            """
            if i % 10 == 0:
                self.generate_excel(mapping_file)
                self.update_progress_bar(i*100/len(liste))
                mapping_file = DataFrame(
                    columns=["Process_filename",
                             "JIRA_key", "Abs_path", "Tree"]
                )

            driver.get(url)
            time.sleep(3)
            tree_span_found = ""

            """
            Grab the tree location of the process
            eg. 1.1 Entreprise Architecture LUX/
            A. Onboarding Activities/
            Client Onboarding/process_name
            """
            try:
                soup = BeautifulSoup(driver.page_source, "lxml")
                tree_spans = soup.find_all(
                    "span", class_="cpn-element-selectable-active"
                )
                tree_span_list = [
                    tree_span.text for tree_span in tree_spans if len(tree_span) > 0
                ]
                tree_span_found = self.find_sub_group(tree_span_list)
                if len(tree_span_found) == 0:
                    tree_span_found = "other"

            except NoSuchElementException:
                pass
            except ElementNotVisibleException:
                pass

            """
            Grab the title of the process from the DOM
            """
            try:
                filename = (
                    self.sanitize(
                        driver.find_element_by_xpath(
                            "//h1[@class='pageTitle']").text
                    )
                    + ".xls"
                )
            except NoSuchElementException:
                logging.getLogger(self.script_name).error(f"404")
                continue

            """
            Grab the mapping file and add the process name if it the url is new
            """
            previous = self.load_mapping_file()
            previous.set_index("Unnamed: 0", inplace=True)
            if url not in previous.index:
                mapping_file.at[url, "Process_filename"] = filename
                mapping_file.at[url, "Tree"] = tree_span_found

            """
            If file already downloaded skip to the next url in the "liste"
            """

            already_downloaded = os.path.isfile(
                os.path.join(self.parent, self.master,
                             self.download_folder, filename)
            )
            if already_downloaded:
                continue

            """
            Find the report icon
            """
            try:
                report_icon = driver.find_element_by_xpath(
                    "//span[@class='icon iconlib_show_report_result_16']"
                )
            except NoSuchElementException:
                continue
            except ElementNotVisibleException:
                pass

            """
            Click on the report icon if the window is "inactive"
            """
            window_is_active = driver.find_element_by_xpath(
                "//li[@data-original-title='Reports']"
            )
            window_is_active = window_is_active.get_attribute(name="class")

            if window_is_active == "list-item":
                report_icon.click()
            # gwt-uid-1053
            time.sleep(5)

            """
            Find the report name and select the
            'Output model information' option
            """
            try:
                report_name = driver.find_element_by_xpath(
                    "//input[@aria-label='Select report script to run']"
                )
                report_name.click()
                time.sleep(1)
                report_name.send_keys(100 * Keys.BACKSPACE)
                time.sleep(3)
                report_name.send_keys("Output model information")
                report_name.send_keys(Keys.ENTER)

            except WebDriverException:
                pass

            time.sleep(1)

            """
            Open the drop down list of file formats
            """
            try:
                report_format = driver.find_element_by_xpath(
                    "//input[@aria-label='Select report format']"
                )
                report_format.click()
            except NoSuchElementException:
                pass
            except ElementNotVisibleException:
                pass
            time.sleep(1)

            """
            Choose the right output file format
            """
            try:
                report_format = driver.find_element_by_xpath(
                    "//a[@title='Output XLS']")
                report_format.click()
            except NoSuchElementException:
                pass
            except ElementNotVisibleException:
                pass
            time.sleep(15)
            """
            Click on start to ask ARIS to compute the excel report
            """
            try:
                start = driver.find_element_by_xpath(
                    "//a[@aria-label='Start']")
                start.click()
            except NoSuchElementException:
                pass
            except ElementNotVisibleException:
                pass
            time.sleep(22)

            """
            Hit the start download
            """
            try:
                start_dl = driver.find_element_by_xpath(
                    "//a[@aria-label='Download result']"
                )
                start_dl.click()
            except NoSuchElementException:
                pass
            except ElementNotVisibleException:
                pass
            time.sleep(1)

            """
            Rename the downloaded file with the "filename" variable
            """
            self.rename(filename)

            """
            Grab the mapping file and add the process name + abs path
            if it the url is new
            """
            if url not in previous.index:
                mapping_file.at[url, "Process_filename"] = filename
                mapping_file.at[url, "Abs_path"] = self.grab_exi_file_path(
                    filename)
                mapping_file.at[url, "Tree"] = tree_span_found

            """
            If browser window is still displaying the download pop up
            for some unknown reason, close it
            """

            try:
                dw_window_is_active = driver.find_element_by_xpath(
                    "//div[@class='modal modal-dialog message-dialog in']"
                )
                dw_window_is_active = dw_window_is_active.get_attribute(
                    name="aria-hidden"
                )
                if dw_window_is_active == "false":
                    close_popup = driver.find_element_by_xpath(
                        "//a[@id='gwt-debug-OK']"
                    )
                    close_popup.click()
            except NoSuchElementException:
                pass
            except ElementNotVisibleException:
                pass

        return mapping_file

    def check_download_folder_exists(self) -> None:
        """
        Utility function that creates the main download folder
        if the folder does not exist
        """
        folder = os.path.join(self.parent, self.master, self.download_folder)
        if os.path.isdir(folder) is False:
            os.mkdir(folder)
            logging.getLogger(self.script_name).info(
                f"Folder name '{self.download_folder}' does not exist,creating"
            )

    def generate_excel(self, df: DataFrame) -> None:
        "Generate an excel from the df provided in the grab_report method"
        writer = pd.ExcelWriter(
            self.mapping, engine="xlsxwriter", options={"remove_timezone": True}
        )
        df.to_excel(writer, sheet_name="mapping", header=True, index=True)
        self.save_excel(writer, df)

    def save_excel(self, writer: ExcelWriter, new_mapping: DataFrame) -> None:
        """ Save the generated excel """
        if new_mapping.shape[1] > 4:
            new_mapping.set_index("Unnamed: 0", inplace=True)
        path_to_mapping = os.path.join(self.parent, self.master, self.mapping)
        if os.path.exists(path_to_mapping):

            logging.getLogger(self.script_name).info(
                f"Folder name '{self.mapping}' already exists, updating file"
            )

            previous = self.load_mapping_file()
            previous.set_index("Unnamed: 0", inplace=True)
            if new_mapping.empty is False:
                result = pd.concat([previous, new_mapping])
                result.to_excel(writer, sheet_name="mapping",
                                header=True, index=True)
                os.chdir(os.path.join(self.parent, self.master))
                writer.save()
                os.chdir(os.path.join(self.parent, self.apps))
        else:
            logging.getLogger(self.script_name).info(
                f"File '{self.mapping}' does not exist, creating"
            )
            os.chdir(os.path.join(self.parent, self.master))
            writer.save()
            os.chdir(os.path.join(self.parent, self.apps))

    def run(self):
        driver, _, _ = self.launch_firefox()
        self.handle_QMessageBox_upstream_requests()
        path_to_mapping = os.path.join(self.parent, self.master, self.mapping)
        if self.skip_url_retrieval is True and os.path.isfile(path_to_mapping):
            input(f"""
                - Login to ARIS
                - This script will update the {self.mapping} file

                Press any key continue to resume
                """
                  )
        if self.skip_url_retrieval is True and os.path.isfile(path_to_mapping) is False:
            input(f"""
                - Login to ARIS
                - This script will create the {self.mapping} file

                Press any key continue to resume
                """
                  )
        if self.skip_url_retrieval is False and os.path.isfile(path_to_mapping):
            input(f"""
                - Login to ARIS
                - And reload the search on the term you need to scrape from
                - This script will update the {self.mapping} file

                Press any key continue to resume
                """
                  )
        if self.skip_url_retrieval is False and os.path.isfile(path_to_mapping) is False:
            input(f"""
                - Login to ARIS
                - And reload the search on the term you need to scrape from
                - This script will create the {self.mapping} file

                Press any key continue to resume
                """
                  )
        if self.skip_url_retrieval is False:
            liste = self.grab_urls(driver, list())
            liste = self.next_page(driver, liste)
            print(f"{len(liste)} urls were saved on your {self.pickle_file}")
            self.save_pickle(liste)
        liste = self.load_pickle()
        self.totalRequest = len(liste)
        self.check_download_folder_exists()
        mapping_file = self.grab_report(liste, driver)
        self.generate_excel(mapping_file)
        self.update_progress_bar(100)
        self.statusbar.showMessage("Done")


def main():
    scraper = Scrape_ARIS()
    scraper.run()


if __name__ == "__main__":
    main()
