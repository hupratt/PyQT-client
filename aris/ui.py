import sys
import os
import yaml
from pyqtconfig import ConfigManager
from typing import Dict, List, Any, Tuple
from PyQt5 import QtCore, QtGui, QtWidgets
import threading

# for the pyinstaller to grab the imports
import scrape_aris
import create_tcs
import sync
import reporting_apps
import reporting_biewer


class Ui_MainWindow(object):

    def initUI(self, MainWindow) -> None:
        """
        Initialize the UI elements
        """

        MainWindow.setWindowTitle(MainWindow.title)
        MainWindow.setWindowIcon(
            QtGui.QIcon(
                os.path.join(MainWindow.apps, "confluence.jpg")
            )
        )
        MainWindow.setGeometry(
            MainWindow.left, MainWindow.top, MainWindow.width, MainWindow.height)

        MainWindow.config.set_defaults(
            MainWindow.aris_config_no_tooltips
        )
        gd = QtWidgets.QGridLayout()
        self.init_ProgressBar(MainWindow, gd)
        self.init_buttons(MainWindow, gd)
        self.init_input_boxes(MainWindow, gd)
        self.init_current_config_output(MainWindow, gd)

    def init_ProgressBar(self, MainWindow, gd):
        MainWindow.setObjectName("MainWindow")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        gd.addWidget(self.progressBar, len(
            MainWindow.aris_config_list)+1, 0, 1, 20)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setRange(0, 100)

    def init_current_config_output(self, MainWindow, gd) -> None:
        """
        Initialize the ouput box
        """
        self.current_config_output = QtWidgets.QTextEdit()
        gd.addWidget(self.current_config_output, 0, 3, 20, 1)
        self.window = QtWidgets.QWidget()
        self.window.setLayout(gd)
        MainWindow.setCentralWidget(self.window)

    def init_input_boxes(self, MainWindow, gd) -> None:
        """
        Initialize the input boxes
        """
        for i, config in enumerate(MainWindow.aris_config_list):
            key, tooltip = config
            if key == "combo":
                map_dict = {
                    'LUXEMBOURG': MainWindow.LUXEMBOURG,
                    'MONACO': MainWindow.MONACO,
                    'NASSAU': MainWindow.NASSAU,
                    'GERMANY': MainWindow.GERMANY
                }
                self.cmb = QtWidgets.QComboBox()
                self.cmb.addItems(map_dict.keys())
                label = QtWidgets.QLabel(str(key) + ": " + str(tooltip))
                id = QtWidgets.QLabel(str(i+1), styleSheet="color: #999999;")
                gd.addWidget(label, i, 1)
                gd.addWidget(id, i, 0)
                gd.addWidget(self.cmb, i, 2)
                MainWindow.config.add_handler(
                    'combo', self.cmb, mapper=map_dict)
            else:
                lineEdit = QtWidgets.QLineEdit()
                label = QtWidgets.QLabel(str(key) + ": " + str(tooltip))
                id = QtWidgets.QLabel(str(i+1), styleSheet="color: #999999;")
                gd.addWidget(label, i, 1)
                gd.addWidget(lineEdit, i, 2)
                gd.addWidget(id, i, 0)
                MainWindow.config.add_handler(key, lineEdit)

    def init_buttons(self, MainWindow, gd) -> None:
        """
        Initialize the buttons and connect them to their methods
        """
        _docstring_scrape = scrape_aris.Scrape_ARIS.__doc__
        _docstring_create = create_tcs.CreateTCS.__doc__
        _docstring_sync = sync.SyncJIRA.__doc__

        self.scrape_ARIS_widget = QtWidgets.QPushButton(
            "Download data from ARIS", self)
        self.create_TC_widget = QtWidgets.QPushButton(
            "Create Test cases on JIRA", self)
        self.sync_TC_widget = QtWidgets.QPushButton(
            "Sync ARIS and JIRA", self)

        self.scrape_ARIS_widget.setToolTip(_docstring_scrape)
        self.create_TC_widget.setToolTip(_docstring_create)
        self.sync_TC_widget.setToolTip(_docstring_sync)

        gd.addWidget(self.scrape_ARIS_widget, len(
            MainWindow.aris_config_list)/2-1, 4)
        gd.addWidget(self.create_TC_widget,
                     (len(MainWindow.aris_config_list)/2), 4)
        gd.addWidget(self.sync_TC_widget,
                     (len(MainWindow.aris_config_list)/2)+1, 4)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        self.LUXEMBOURG = "LUXEMBOURG"
        self.MONACO = "MONACO"
        self.NASSAU = "NASSAU"
        self.GERMANY = "GERMANY"

        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.title = "ARIS - JIRA Interface GUI"
        self.left, self.top, self.width, self.height = (0, 30, 1600, 480)
        self.config = ConfigManager()
        self.aris_config = self.open_conf_lux()
        self.apps = os.path.join(os.path.dirname(
            os.getcwd()), self.aris_config["apps"][0])
        self.aris_config_no_tooltips = {key: val[0]
                                        for (key, val) in self.aris_config.items()}
        self.aris_config_list = [(key, value[1])
                                 for key, value in self.aris_config.items()]
        self.initUI(self)
        self.statusBar().showMessage("Ready.")

        self.scrape_ARIS_widget.clicked.connect(self.scrape_ARIS)
        self.create_TC_widget.clicked.connect(self.create_TC)
        self.sync_TC_widget.clicked.connect(self.sync_TC)
        self.config.updated.connect(self.show_config)
        self.config.updated.connect(self.save_config)
        self.cmb.activated[str].connect(self.load_preconfigured_json)
        self.event_stop = threading.Event()
        QtWidgets.QShortcut("Ctrl+C", self, activated=self.end_button_func)

    def load_preconfigured_json(self, text):
        if text == "MONACO":
            self.config.config = {key: val[0]
                                  for (key, val) in self.open_conf_mco().items()}
            self.save_config()
            self.show_config()

        elif text == "LUXEMBOURG":
            self.config.config = {key: val[0]
                                  for (key, val) in self.open_conf_lux().items()}
            self.save_config()
            self.show_config()

        elif text == "NASSAU":
            self.config.config = {key: val[0]
                                  for (key, val) in self.open_conf_nas().items()}
            self.save_config()
            self.show_config()

        elif text == "GERMANY":
            self.config.config = {key: val[0]
                                  for (key, val) in self.open_conf_ger().items()}
            self.save_config()
            self.show_config()

    def scrape_ARIS(self) -> None:
        self.would_like_to_clear_everything_scrape()
        if self.config.config["would_like_to_clear_everything_scrape"] is False:
            self.would_like_to_delete_all_xls_files_from_temp_and_download()
            self.would_like_delete_mapping_file()
            self.would_like_delete_pickle()
            self.would_like_to_skip_url_retrieval()
        self.save_config()
        # Instantiate and feed the progress bar to the scraper instance to get real time data
        self.statusBar().showMessage("Program paused, please refer to the console")
        runnable = scrape_aris.Scrape_ARIS(self.progressBar, self.statusBar())
        # Execute
        QtCore.QThreadPool.globalInstance().start(runnable)

    def sync_TC(self) -> None:
        # Instantiate and feed the progress bar to the scraper instance to get real time data
        runnable = sync.SyncJIRA(self.progressBar, self.statusBar())
        # Execute
        QtCore.QThreadPool.globalInstance().start(runnable)

    def create_TC(self) -> None:
        # notifications
        self.would_like_to_clear_everything_create()
        if self.config.config["would_like_to_clear_everything_create"] is False:
            self.would_like_delete_json_dump_file()
            self.would_like_delete_xlsx_files()
        self.save_config()

        # Instantiate and feed the progress bar to the creator instance to get real time data
        self.statusBar().showMessage("Program paused, please refer to the console")
        runnable = create_tcs.CreateTCS(self.progressBar, self.statusBar())
        # Execute
        QtCore.QThreadPool.globalInstance().start(runnable)

    @QtCore.pyqtSlot()
    def save_config(self) -> None:
        """
        Once edited, the config file is stored in a yml file that will be used by the apps
        """
        with open("generated_config_aris.yml", "w") as file:
            yaml.dump(self.config.config, file)

    @QtCore.pyqtSlot()
    def end_button_func(self):
        self.event_stop.set()

    def show_config(self) -> None:
        self.current_config_output.setText(str(self.config.as_dict()))

    def open_conf_lux(self) -> Dict[str, Tuple[str, str]]:
        """
        load LUX default parameters
        """
        return {
            "combo": (self.LUXEMBOURG, "Choose a configuration pre-set or manually configure it through the input boxes below"),
            "FirefoxBinary": ("FirefoxPortableESR\\App\\Firefox64\\firefox.exe", "firefox binaries location"),
            "Geckodriver_binary": ("FirefoxPortableESR\\geckodriver\\geckodriver.exe", "firefox driver location"),
            "search_value": ("lux", "search term that you will search for on ARIS"),
            "log_name": ("aris lux.log", "log name of all scripts in this app"),
            "mapping_file_name": ("mapping -lux.xlsx", "db that holds the 1 to 1 relationship between ARIS id and JIRA id"),
            "target": ("https://jira-uat4.com/", "url for ticket creation and sync"),
            "config_path": ("C:\\Users\\u46022\\Documents", "path that holds a configuration.py file that holds sensitive credentials"),
            "master": ("ARIS", "master path that holds all of the downloads and the mapping file"),
            "apps": ("ARIS_apps", "master path that holds all of the scripts logs, intermediary pickles as well as consolidated xls and csv files"),
            "json_dump_file": ("data lux.json", "Pickle that holds all of the consolidated data. This is an important input for the sync script"),
            "reporting": ("reporting", "path to reporting folder"),
            "process_url": ("http://srp07000wn.com/#default/item/", "specific ARIS url to consult a process"),
            "search_url": ("http://srp07000wn.com/#default/search", "ARIS url to perform a search"),
            "pickle_file": ("liste -lux.txt", "pickle that holds all the urls we should visit"),
            "download_folder": ("download lux", "download master folder that holds the renamed processes"),
            "temp_folder": ("temp", "download master folder that holds the soon to be renamed processes"),
            "download_folder": ("download lux", "download master folder that holds the renamed processes"),
            "test_path": ("/Testing/LUX_processes", "specific xray field that creates a tree for the test storage"),
            "JIRA_project": ("T2L", "which jria project should the ticket be created in?"),
            "consolidated_file_name": ("Consolidated_lux", "file name of the consolidated csv and xlsx ouput"),
        }

    def open_conf_mco(self) -> Dict[str, Tuple[str, str]]:
        """
        load MCO default parameters
        """
        return {
            "combo": (self.MONACO, "Choose a configuration pre-set or manually configure it through the input boxes below"),
            "FirefoxBinary": ("FirefoxPortableESR\\App\\Firefox64\\firefox.exe", "firefox binaries location"),
            "Geckodriver_binary": ("FirefoxPortableESR\\geckodriver\\geckodriver.exe", "firefox driver location"),
            "search_value": ("mco", "search term that you will search for on ARIS"),
            "log_name": ("aris mco.log", "log name of all scripts in this app"),
            "mapping_file_name": ("mapping -mco.xlsx", "db that holds the 1 to 1 relationship between ARIS id and JIRA id"),
            "target": ("https://jira-uat4.com/", "url for ticket creation and sync"),
            "config_path": ("C:\\Users\\u46022\\Documents", "path that holds a configuration.py file that holds sensitive credentials"),
            "master": ("ARIS", "master path that holds all of the downloads and the mapping file"),
            "apps": ("ARIS_apps", "master path that holds all of the scripts logs, intermediary pickles as well as consolidated xls and csv files"),
            "json_dump_file": ("data mco.json", "Pickle that holds all of the consolidated data. This is an important input for the sync script"),
            "reporting": ("reporting", "path to reporting folder"),
            "process_url": ("http://srp07000wn.com/#default/item/", "specific ARIS url to consult a process"),
            "search_url": ("http://srp07000wn.com/#default/search", "ARIS url to perform a search"),
            "pickle_file": ("liste -mco.txt", "pickle that holds all the urls we should visit"),
            "download_folder": ("download mco", "download master folder that holds the renamed processes"),
            "temp_folder": ("temp", "download master folder that holds the soon to be renamed processes"),
            "download_folder": ("download mco", "download master folder that holds the renamed processes"),
            "test_path": ("/Testing/MCO_processes", "specific xray field that creates a tree for the test storage"),
            "JIRA_project": ("T2L", "which jria project should the ticket be created in?"),
            "consolidated_file_name": ("Consolidated_mco", "file name of the consolidated csv and xlsx ouput"),
        }

    def open_conf_nas(self) -> Dict[str, Tuple[str, str]]:
        """
        load NASSAU default parameters
        """
        return {
            "combo": (self.NASSAU, "Choose a configuration pre-set or manually configure it through the input boxes below"),
            "FirefoxBinary": ("FirefoxPortableESR\\App\\Firefox64\\firefox.exe", "firefox binaries location"),
            "Geckodriver_binary": ("FirefoxPortableESR\\geckodriver\\geckodriver.exe", "firefox driver location"),
            "search_value": ("nas", "search term that you will search for on ARIS"),
            "log_name": ("aris nas.log", "log name of all scripts in this app"),
            "mapping_file_name": ("mapping -nas.xlsx", "db that holds the 1 to 1 relationship between ARIS id and JIRA id"),
            "target": ("https://jira-uat4.com/", "url for ticket creation and sync"),
            "config_path": ("C:\\Users\\u46022\\Documents", "path that holds a configuration.py file that holds sensitive credentials"),
            "master": ("ARIS", "master path that holds all of the downloads and the mapping file"),
            "apps": ("ARIS_apps", "master path that holds all of the scripts logs, intermediary pickles as well as consolidated xls and csv files"),
            "json_dump_file": ("data nas.json", "Pickle that holds all of the consolidated data. This is an important input for the sync script"),
            "reporting": ("reporting", "path to reporting folder"),
            "process_url": ("http://srp07000wn.com/#default/item/", "specific ARIS url to consult a process"),
            "search_url": ("http://srp07000wn.com/#default/search", "ARIS url to perform a search"),
            "pickle_file": ("liste -nas.txt", "pickle that holds all the urls we should visit"),
            "download_folder": ("download nas", "download master folder that holds the renamed processes"),
            "temp_folder": ("temp", "download master folder that holds the soon to be renamed processes"),
            "download_folder": ("download nas", "download master folder that holds the renamed processes"),
            "test_path": ("/Testing/NAS_processes", "specific xray field that creates a tree for the test storage"),
            "JIRA_project": ("T2L", "which jria project should the ticket be created in?"),
            "consolidated_file_name": ("Consolidated_nas", "file name of the consolidated csv and xlsx ouput"),
        }

    def open_conf_ger(self) -> Dict[str, Tuple[str, str]]:
        """
        load GERMANY default parameters
        """
        return {
            "combo": (self.GERMANY, "Choose a configuration pre-set or manually configure it through the input boxes below"),
            "FirefoxBinary": ("FirefoxPortableESR\\App\\Firefox64\\firefox.exe", "firefox binaries location"),
            "Geckodriver_binary": ("FirefoxPortableESR\\geckodriver\\geckodriver.exe", "firefox driver location"),
            "search_value": ("ger", "search term that you will search for on ARIS"),
            "log_name": ("aris ger.log", "log name of all scripts in this app"),
            "mapping_file_name": ("mapping -ger.xlsx", "db that holds the 1 to 1 relationship between ARIS id and JIRA id"),
            "target": ("https://jira-uat4.com/", "url for ticket creation and sync"),
            "config_path": ("C:\\Users\\u46022\\Documents", "path that holds a configuration.py file that holds sensitive credentials"),
            "master": ("ARIS", "master path that holds all of the downloads and the mapping file"),
            "apps": ("ARIS_apps", "master path that holds all of the scripts logs, intermediary pickles as well as consolidated xls and csv files"),
            "json_dump_file": ("data ger.json", "Pickle that holds all of the consolidated data. This is an important input for the sync script"),
            "reporting": ("reporting", "path to reporting folder"),
            "process_url": ("http://srp07000wn.com/#default/item/", "specific ARIS url to consult a process"),
            "search_url": ("http://srp07000wn.com/#default/search", "ARIS url to perform a search"),
            "pickle_file": ("liste -ger.txt", "pickle that holds all the urls we should visit"),
            "download_folder": ("download ger", "download master folder that holds the renamed processes"),
            "temp_folder": ("temp", "download master folder that holds the soon to be renamed processes"),
            "download_folder": ("download ger", "download master folder that holds the renamed processes"),
            "test_path": ("/Testing/GER_processes", "specific xray field that creates a tree for the test storage"),
            "JIRA_project": ("T2L", "which jria project should the ticket be created in?"),
            "consolidated_file_name": ("Consolidated_ger", "file name of the consolidated csv and xlsx ouput"),
        }

    def would_like_delete_pickle(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would you like to delete the pickle_file?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config["delete_pickle"] = True
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config["delete_pickle"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_to_skip_url_retrieval(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would you like to skip url retrieval and jump straight into ARIS download?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config["skip_url_retrieval"] = True
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config["skip_url_retrieval"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_to_delete_all_xls_files_from_temp_and_download(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would like to delete all xls files from temp and download?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config[
                "delete_all_xls_files_from_temp_and_download"] = True
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config[
                "delete_all_xls_files_from_temp_and_download"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_delete_mapping_file(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would you like to delete the mapping_file?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config["delete_mapping_file"] = True
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config["delete_mapping_file"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_delete_json_dump_file(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would you like to delete the json database file?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config["delete_json_dump_file"] = True
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config["delete_json_dump_file"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_delete_xlsx_files(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would like to delete all xlsx files from the download folder?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config[
                "delete_all_xlsx_files_from_temp_and_download"] = True
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config[
                "delete_all_xlsx_files_from_temp_and_download"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_to_clear_everything_scrape(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would you like to clear everything and start a fresh scrape?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config[
                "would_like_to_clear_everything_scrape"] = True
            self.config.config["delete_mapping_file"] = False
            self.config.config[
                "delete_all_xls_files_from_temp_and_download"] = False
            self.config.config["skip_url_retrieval"] = False
            self.config.config["delete_pickle"] = False
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config[
                "would_like_to_clear_everything_scrape"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()

    def would_like_to_clear_everything_create(self) -> None:
        assert isinstance(self.config.config, dict)
        buttonReply = QtWidgets.QMessageBox.question(self, self.title, "Would you like to clear everything and start a fresh test case creation?",
                                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if buttonReply == QtWidgets.QMessageBox.Yes:
            self.config.config[
                "would_like_to_clear_everything_create"] = True
            self.config.config[
                "delete_all_xlsx_files_from_temp_and_download"] = False
            self.config.config["delete_json_dump_file"] = False
        elif buttonReply == QtWidgets.QMessageBox.No:
            self.config.config[
                "would_like_to_clear_everything_create"] = False
        elif buttonReply == QtWidgets.QMessageBox.Cancel:
            sys.exit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    _MainWindow = MainWindow()
    _MainWindow.show()
    sys.exit(app.exec_())
