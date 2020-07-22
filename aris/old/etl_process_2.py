import pandas as pd
import atlassian, json, os, logging
from utils import Loader
from numpy import nan

    
def search_import_file(extension):
    _directory = [i for i in os.listdir(os.path.curdir)]
    path_to_files = list()
    curdir = os.path.abspath(os.path.curdir)
    for file in _directory: 
        if file.endswith(extension):
            path_to_files.append(os.path.join(curdir,file))
    return path_to_files

def load():
    loader = Loader()
    jira = atlassian.Jira(url = "https://jira", username = loader.cfg.user, password = loader.cfg.password)
    return jira

def setLogger() -> logging.Logger:
    ''' check if FileHandler exists'''
    ''' FileHandler is created at python level and not @ the level of this class '''
    if (len(logging.getLogger(__name__).handlers) == 0):
        ''' Instantiate the FileHandler aka logger object so that it records general info and exceptions into a .log file '''
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        ''' create a file handler '''
        handler = logging.FileHandler('aris.log')
        handler.setLevel(logging.INFO)
        ''' create a logging format '''
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        ''' add the handlers to the logger '''
        logger.addHandler(handler)
        return logger
        
def main():
    setLogger()
    consolidated = search_import_file(".json")
    if len(consolidated) > 1:
        raise ValueError("Too many files to choose from. There should only be one consolidated DB")
    path_to_consolidated = consolidated[0]

    with open(path_to_consolidated) as json_file:
        data = json.load(json_file)
 
    parent = os.getcwd()
    path_to_mapping = os.path.join(parent, "ARIS", "mapping.xlsx")
    df_mapping = pd.read_excel(path_to_mapping, sheet_name="Reports")
    JIRA_keys = df_mapping["JIRA_Key"].to_list()
    jira = load()
    for JIRA_key in JIRA_keys:
        if JIRA_key is not nan:
            online_version = jira.issue_fields(JIRA_key)
            description = online_version["description"]
            offline_version = data[0][description]
            if description != offline_version["description"]:
                print("found diff")
            responsible = online_version["customfield_15380"]['name']
            if responsible != offline_version["customfield_15380"]['name']:
                print("found diff")
            assignee = online_version["assignee"]['name']
            if assignee != offline_version["assignee"]['name']:
                print("found diff")
            reporter = online_version["reporter"]['name']
            if reporter != offline_version["reporter"]['name']:
                print("found diff")
            priority = online_version["priority"]['name']
            if priority != offline_version["priority"]['name']:
                print("found diff")
            application = online_version["customfield_16181"]
            if application != offline_version["customfield_16181"]:
                print("found diff")
            summary = online_version["summary"]
            if summary != offline_version["summary"]:
                print("found diff")
            steps = online_version["customfield_17284"]
            online_steps_list = [test_step['step'] for test_step in steps['steps']]
            steps = offline_version["customfield_17284"]
            offline_steps_list = [test_step['step'] for test_step in steps['steps']]
            if offline_steps_list != online_steps_list:
                print("found diff")
            location = online_version["customfield_17291"]
            if location != offline_version["customfield_17291"]:
                print("found diff") 
    logging.getLogger(__name__).info(f'Log working')


if __name__ == "__main__":
    main()


