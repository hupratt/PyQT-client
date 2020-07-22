import time, logging, os
import pandas as pd
from requests.exceptions import ConnectionError
from base_class import BaseExtractor
from pandas import DataFrame
from typing import Union
from decorator_base import Memorize
from utils import MyDefaultDict

NAME = 'JIRA_UAT_Deploy-Log'


class DeployExtractor(BaseExtractor):
    
    def __init__(self, name: str, verbose = None) -> None:
        super().__init__(name = name, verbose = verbose) 
        ''' constants '''
        self.URL = self.yml['deploy']['URL_1'] + self.yml['deploy']['JQL'] + str(self.yml['deploy']['URL_2'])
        self.search = self.URL + self.yml['jira']['LINK'] + str(self.yml['jira']['START_AT'])
        
    def custom_validation(self, envs: list) -> None:
        for element in ['EU UAT Deployment Date','EU TEST Deployment Date', 'PRD Deployment Date']:
            if element not in envs:
                message = "{} is not available in the 'dataframe' column index: {}".format(element, envs)
                raise Exception(message)
                logging.getLogger(__name__).error(message)
    
    def identify_missing_links(self, dataframe: DataFrame, envs: list) -> DataFrame:
        ''' Business Logic, if the package was deployed in PRD a JIRA link should populate the UAT and TEST environment date fields'''
        ''' Same thing for UAT, if the package was deployed in UAT a JIRA link should populate the TEST environment date fields'''
        
        self.custom_validation(envs)
        
        new_dataframe = pd.isnull(dataframe[['EU UAT Deployment Date','EU TEST Deployment Date']])
        new_dataframe = new_dataframe[new_dataframe['EU UAT Deployment Date']==False]
        new_dataframe = new_dataframe[new_dataframe['EU TEST Deployment Date']==True]
        dataframe.loc[new_dataframe.index,'EU TEST Deployment Date'] = 'Missing link to the UAT deployment ticket'

        new_dataframe = pd.isnull(dataframe[['PRD Deployment Date','EU UAT Deployment Date','EU TEST Deployment Date']])
        new_dataframe = new_dataframe[new_dataframe['PRD Deployment Date']==False]
        new_dataframe = new_dataframe[new_dataframe['EU TEST Deployment Date']==True]
        dataframe.loc[new_dataframe.index,'EU TEST Deployment Date'] = 'Missing link to the UAT deployment ticket'
        
        new_dataframe = pd.isnull(dataframe[['PRD Deployment Date','EU UAT Deployment Date','EU TEST Deployment Date']])
        new_dataframe = new_dataframe[new_dataframe['PRD Deployment Date']==False]
        new_dataframe = new_dataframe[new_dataframe['EU UAT Deployment Date']==True]
        dataframe.loc[new_dataframe.index,'EU UAT Deployment Date'] = 'Missing link to the PRD deployment ticket'
        
        return dataframe
    
    def generate_excel(self, dictionary: dict, envs: list) -> None:
        ''' Generate an excel from the dictionary provided in the input section '''
        ''' Transform certain columns into datetime objects so that excel can sort them properly ''' 
        
        timerz=time.strftime("%Y%m%d_%H%M%S_"+str(len(dictionary)))
        filename = str(self.name)+'_'+timerz+'.xlsx'
        df = pd.DataFrame.from_dict(dictionary,orient='index')
        for env in envs:
            df[env] = pd.to_datetime(df[env], format="%Y/%m/%d", errors='ignore', utc=True)
            df[env] = df[env].apply(lambda x: x.tz_convert('Europe/Luxembourg'))

        writer = pd.ExcelWriter(filename, engine='xlsxwriter', options={'remove_timezone': True})
        df = self.identify_missing_links(df, envs)
        df.to_excel(writer, sheet_name=self.name, header=True, index=True)
        # Close the Pandas Excel writer and output the Excel file
        self.save_excel(writer)
        self.test_file_creation

#    @Memorize(func_name = "grab_tickets", file_name = os.path.basename(__file__))
    def grab_tickets(self, dictionary: dict) -> dict:
        return super().grab_tickets(dictionary)
    
#    @Memorize(func_name = "clean_json", file_name = os.path.basename(__file__))
    def clean_json(self, dictionary: dict) -> Union[DataFrame, list]:
        ''' Mapping function '''
        ''' Go through the json and pick the right values to add to the excel ''' 
        '''
        # Applications: customfield_12705
        # Deployment duration: customfield_13180
        # Target environment: customfield_11880
        # Deployment Type: customfield_16880
        # PSP: customfield_12706
        # Deployment Time : customfield_10091
        '''
        
        final_json = dict()
        envs = list()
        for jira_key, val in dictionary.items():
            json_trash = dict()
            val_ = MyDefaultDict(val)
            val = val_
            environment_acronym = val['customfield_11880'][0]['value']
            json_trash['Target Environment'] = environment_acronym
            json_trash['Summary'] = val['summary']
            # json_trash['Description'] = val['description']
            json_trash['Reporter'] = val['reporter']['displayName']
            if val['assignee'] is not None:
                json_trash['Assignee'] = val['assignee']['displayName']
            json_trash['Status'] = val['status']['name']
            json_trash['Deployment Duration'] = val['customfield_13180']
            if len(val['customfield_12705']) > 0:
                json_trash['Applications'] = val['customfield_12705'][0]
            if val['customfield_16880'] is not None:
                json_trash['Deployment Type'] = val['customfield_16880']['value']
            if len(val['customfield_12706']) > 0:
                json_trash['PSP'] = val['customfield_12706'][0]
            
            if isinstance(environment_acronym, str):
                deploy_env = environment_acronym + ' Deployment Date'
                if 'PRD' not in deploy_env:
                    ''' append column name so that it can be formatted as date in the generate_excel method '''
                    envs.append(deploy_env)
                json_trash[deploy_env] = val['customfield_10091']
            
            ''' handle the linked tickets so that we can grab their deploy date '''
            liste = list()
            if len(val['issuelinks']) > 0:
                for i in range(len(val['issuelinks'])):
                    try:
                        liste.append(self.cfg.BASE_URL + val['issuelinks'][i]['inwardIssue']['key'])
                    except KeyError:
                        pass
                    try:
                        liste.append(self.cfg.BASE_URL + val['issuelinks'][i]['outwardIssue']['key'])
                    except KeyError:
                        pass
            for i in range(len(liste)):
                try:
                    '''
                    # Other scripts query the API 3 times at most
                    # I'm mitigating the potential denial of service here with the 1 second sleep as the total number of queries can potentially be high. 
                    # The total number of queries is increased by the number of issue links. 
                    '''
                    if len(liste) > 1:
                        ticket = self.grab_linked_tickets(liste)
                    else:
                        ticket = self.consult_url(liste[0]).json()
                    issuetype = ticket['fields']['issuetype']['name']
                    if issuetype == "Normal Change" or issuetype == "Standard Change":
                        ''' Grab 'start date and time' from CM '''
                        json_trash['PRD Deployment Date'] = ticket['fields']['customfield_11483']
                        ''' Append column name so that it can be formatted as date in the generate_excel method '''
                        envs.append('PRD Deployment Date')
                    if issuetype == "Deployment":
                        environment_acronym = ticket['fields']['customfield_11880'][0]['value']                        
                        deploy_env = environment_acronym + ' Deployment Date'
                        json_trash[deploy_env] = ticket['fields']['customfield_10091']
                except ConnectionError as e:
                    if self.verbose is True:
                        print(e)
                    logging.getLogger(__name__).error(f'Connection Error when consulting CM ticket: {e}')
                    raise
                except TypeError as e: # add to TEST
                    if self.verbose is True:
                        print(e)
                    logging.getLogger(__name__).error(f'Could not serialize the payload: {e}')
                    raise
                    
            final_json[jira_key] = json_trash
        return final_json, envs

def main(name):
    ''' Instantiate the Extractor class, grab the tickets from the JIRA API and output an excel '''
    ''' Each user story needs to be packaged and deployed in a certain evironment '''
    ''' This report replaces the excel follow up'''
    extractor = DeployExtractor(name = name)
    
    if extractor.runtests is True:
        extractor.run_tests()
    
    extractor.startTimer
    json = extractor.grab_tickets(dict())
    json = extractor.remove_custom_fields(json, 'customfield_12705', 'customfield_13180', 'customfield_11880', 'customfield_16880', 'customfield_12706', 'customfield_10091')
    json, envs = extractor.clean_json(json)
    extractor.generate_excel(json, envs)
    extractor.closeTimer
    

def test_fixtures(NAME):
    VERBOSE = False
    return DeployExtractor(name = NAME, verbose = VERBOSE)

if __name__ == "__main__":
    main(NAME)

