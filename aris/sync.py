from PyQt5 import QtCore
import pandas as pd
import atlassian
import json
import os
import logging
from numpy import nan
from my_jira_app.utils import MyLogger, Loader, path_leaf
from collections import ChainMap


class SyncJIRA(MyLogger, Loader, QtCore.QRunnable):
    """
    Sync ARIS and JIRA
    """

    def __init__(self, progressbar=None, statusBar=None) -> None:
        QtCore.QRunnable.__init__(self)
        self.progressbar = progressbar
        self.statusbar = statusBar
        self.parent = os.path.dirname(os.getcwd())
        self.yml = self.load_yml("generated_config_aris.yml")
        self.target = self.yml["target"]
        self.log_name = self.yml["log_name"]
        self.mapping = self.yml["mapping_file_name"]
        # Namespace for the logger
        self.script_name = path_leaf(__file__)
        self.json_dump_file = self.yml["json_dump_file"]
        self.config_path = self.yml["config_path"]
        self.wdirectory = os.getcwd()
        self.cfg = self.grab_configuration()
        self.master = self.yml["master"]
        self.apps = self.yml["apps"]

        super().__init__(log_name=self.log_name, name=self.script_name)

    def handle_QMessageBox_upstream_requests(self):
        pass

    def load_json(self):
        path_to_json_dump_file = os.path.join(
            self.parent, self.apps, self.json_dump_file
        )
        with open(path_to_json_dump_file) as json_file:
            list_of_dics = json.load(json_file)
            # convert list of dict into dict
            return dict(ChainMap(*list_of_dics))

    def load_jira_client(self):
        jira = atlassian.Jira(
            url=self.target, username=self.cfg.user, password=self.cfg.password
        )
        return jira

    def grab_jira_keys(self):
        path_to_mapping = os.path.join(self.parent, self.master, self.mapping)
        df_mapping = pd.read_excel(path_to_mapping, sheet_name="mapping")
        return df_mapping["JIRA_key"].to_list()

    def compare_offline_online(self, JIRA_keys, jira, data):
        self.statusbar.showMessage(
            "Comparing offline and online data")
        self.total_tickets = len(JIRA_keys)
        for i, JIRA_key in enumerate(JIRA_keys):
            if JIRA_key is not nan:
                online_version = jira.issue_fields(JIRA_key)
                description = online_version["description"]
                offline_version = data[description]
                if description != offline_version["description"]:
                    logging.getLogger(self.script_name).info(
                        "Description changed")
                    logging.getLogger(self.script_name).info(
                        f'{description} != {offline_version["description"]}'
                    )
                responsible = online_version["customfield_15380"]["name"]
                if responsible != offline_version["customfield_15380"]["name"]:
                    logging.getLogger(self.script_name).info(
                        "Responsible changed")
                    logging.getLogger(self.script_name).info(
                        f'{responsible} != {offline_version["customfield_15380"]["name"]}'
                    )
                assignee = online_version["assignee"]["name"]
                if assignee != offline_version["assignee"]["name"]:
                    logging.getLogger(self.script_name).info(
                        "Assignee changed")
                    logging.getLogger(self.script_name).info(
                        f'{assignee} != {offline_version["assignee"]["name"]}'
                    )

                reporter = online_version["reporter"]["name"]
                if reporter != offline_version["reporter"]["name"]:
                    logging.getLogger(self.script_name).info(
                        "Reporter changed")
                    logging.getLogger(self.script_name).info(
                        f'{reporter} != {offline_version["reporter"]["name"]}'
                    )

                priority = online_version["priority"]["name"]
                if priority != offline_version["priority"]["name"]:
                    logging.getLogger(self.script_name).info(
                        "Priority changed")
                    logging.getLogger(self.script_name).info(
                        f'{priority} != {offline_version["priority"]["name"]}'
                    )

                application = online_version["customfield_16181"]
                if application != offline_version["customfield_16181"]:
                    logging.getLogger(self.script_name).info(
                        "Application changed")
                    logging.getLogger(self.script_name).info(
                        f'{application} != {offline_version["customfield_16181"]}'
                    )

                summary = online_version["summary"]
                if summary != offline_version["summary"]:
                    logging.getLogger(self.script_name).info("Summary changed")
                    logging.getLogger(self.script_name).info(
                        f'{summary} != {offline_version["summary"]}'
                    )

                steps = online_version["customfield_17284"]
                online_steps_list = [test_step["step"]
                                     for test_step in steps["steps"]]
                steps = offline_version["customfield_17284"]
                offline_steps_list = [test_step["step"]
                                      for test_step in steps["steps"]]
                if offline_steps_list != online_steps_list:
                    logging.getLogger(self.script_name).info("Steps changed")
                    logging.getLogger(self.script_name).info(
                        f"{offline_steps_list} != {online_steps_list}"
                    )

                location = online_version["customfield_17291"]
                offline_loc = offline_version["customfield_17291"]
                if location != offline_loc:
                    if offline_loc[-1] == " " and location != offline_loc[:-1]:
                        logging.getLogger(self.script_name).info(
                            f"Location changed")
                        logging.getLogger(self.script_name).info(
                            f'{location} != {offline_version["customfield_17291"]}'
                        )
            self.update_progress_bar((i+1)*100/self.total_tickets, i+1)
        logging.getLogger(self.script_name).info("Sync done")

    def update_progress_bar(self, currentPercentage, num=1):
        if self.statusbar is not None:
            self.statusbar.showMessage(
                f"{self.total_tickets-num-1} test cases left to review")
            QtCore.QMetaObject.invokeMethod(self.progressbar, "setValue",
                                            QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(
                                                int, currentPercentage))

    def run(self):
        self.handle_QMessageBox_upstream_requests()
        logging.getLogger(self.script_name).info(
            "Starting sync.py")
        data = self.load_json()
        JIRA_keys = self.grab_jira_keys()
        jira = self.load_jira_client()
        self.compare_offline_online(JIRA_keys, jira, data)
        self.update_progress_bar(100)
        self.statusbar.showMessage("Done")


def main():
    sync_instance = SyncJIRA()
    sync_instance.run()


if __name__ == "__main__":
    main()
