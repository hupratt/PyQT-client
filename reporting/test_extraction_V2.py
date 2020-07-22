import time, logging, argparse, os
import pandas as pd
from requests.exceptions import ConnectionError
from base_class import BaseExtractor
from pandas import DataFrame
from decorator_base import Memorize, Debug
from utils import MyDefaultDict


NAME = 'JIRA_Test_Report'

class TestExtractor(BaseExtractor):
    
    def __init__(self, name: str, verbose = None):
        super().__init__(name = name, verbose = verbose) 
        ''' These parameters can be overriden by CLI parameters with load_argparser() '''
        self.base_url = self.yml['test']['BASE_URL']
        self.psp = self.yml['test']['PSP']
        ''' constants '''
        self.URL = self.yml['test']['URL_1'] + str(self.psp) + self.yml['test']['URL_2']
        self.search = self.URL + self.yml['jira']['LINK'] + str(self.yml['jira']['START_AT'])
    
    def generate_argparser(self) -> argparse.ArgumentParser:
        parser = super().generate_argparser()
        parser.add_argument('-p', '--psp', choices=['P3304', 'P3356'], help = 'specify the product and service number for the JQL', required=True)
        parser.add_argument('-env', '--environment', help = 'specify the environment where the JQL should run', choices=['PROD', 'UAT'], required=True)
        return parser
    
    def generate_excel(self, dictionary: dict) -> None: 
        ''' Generate an excel from the dictionary provided in the input section '''
        ''' Transform certain columns into datetime objects so that excel can sort them properly ''' 
        
        timerz=time.strftime("%Y%m%d_%H%M%S_"+str(len(dictionary)))
        filename = str(self.name)+'_'+timerz+'.xlsx'
        df = pd.DataFrame.from_dict(dictionary,orient='index')
        ''' Re-order columns in the dataframe '''
        df = df.filter(items=['Issue Type',	'Summary','Status','Reporter','Priority','Assignee','Test data','Test step','Test result','Bug_1_summary','Bug_1_url','Bug_2_summary','Bug_2_url','Bug_4_summary','Bug_4_url','Bug_5_summary','Bug_5_url','Bug_3_summary','Bug_3_url','Bug_6_summary','Bug_6_url','Bug_7_summary','Bug_7_url','Bug_8_summary','Bug_8_url','Bug_9_summary','Bug_9_url','Bug_10_summary','Bug_10_url'])
        df_BLOCKED = df[df['Status'] == 'BLOCKED']
        df_PASS = df[df['Status'] == 'PASS']
        df_EXECUTING = df[df['Status'] == 'EXECUTING']
        df_FAIL = df[df['Status'] == 'FAIL']
        writer = pd.ExcelWriter(filename, engine='xlsxwriter', options={'remove_timezone': True})
        df_BLOCKED.to_excel(writer, sheet_name='BLOCKED', header=True, index=True)
        df_PASS.to_excel(writer, sheet_name='PASS', header=True, index=True)
        df_EXECUTING.to_excel(writer, sheet_name='EXECUTING', header=True, index=True)
        df_FAIL.to_excel(writer, sheet_name='FAIL', header=True, index=True)
        
        ''' Close the Pandas Excel writer and output the Excel file '''
        self.save_excel(writer)
        self.test_file_creation

    @Memorize(func_name = "grab_tickets", file_name = os.path.basename(__file__))
    def grab_tickets(self, dictionary: dict) -> dict:
        return super().grab_tickets(dictionary) 
    
#    @Memorize(func_name = "clean_json", file_name = os.path.basename(__file__))
    def clean_json(self, dictionary: dict) -> DataFrame:
        ''' Mapping function '''
        ''' Go through the json and pick the right values to add to the excel ''' 
        # Steps: customfield_17284
        # Xray status: customfield_17290
        final_json = dict()
        for jira_key, val in dictionary.items():
            json_trash = dict()
            val_ = MyDefaultDict(val)
            val = val_

            json_trash['Summary'] = val['summary']
            json_trash['Reporter'] = val['reporter']['displayName']
            json_trash['Issue Type'] = val['issuetype']['name']
            json_trash['Status'] = val['status']['name']
            
            ''' Test step '''
            if 'step' in val['customfield_17284']['steps'][0]:
                json_trash['Test step'] = val['customfield_17284']['steps'][0]['step']
                
            ''' Test result '''    
            if 'result' in val['customfield_17284']['steps'][0]:
                json_trash['Test result'] = val['customfield_17284']['steps'][0]['result']
                
            ''' Test data '''
            if 'data' in val['customfield_17284']['steps'][0]:
                json_trash['Test data'] = val['customfield_17284']['steps'][0]['data']
                
            ''' Assignee '''
            if val['assignee'] is not None:
                json_trash['Assignee'] = val['assignee']['displayName']
                
            ''' Priority '''
            if val['priority'] is not None:
                json_trash['Priority'] = val['priority']['name']
            
            ''' Grab test execution status '''
            if json_trash['Issue Type'] == 'Test':
                if val['customfield_17290']['statuses'][0]['statusResults'] is not None:
                    if val['customfield_17290']['statuses'][0]['statusResults'][0]['latest'] == 1000:
                        json_trash['Status'] = 'BLOCKED'
                    if val['customfield_17290']['statuses'][0]['statusResults'][0]['latest'] == 0:
                        json_trash['Status'] = 'PASS'
                    if val['customfield_17290']['statuses'][0]['statusResults'][0]['latest'] == 2:
                        json_trash['Status'] = 'EXECUTING'
                    if val['customfield_17290']['statuses'][0]['statusResults'][0]['latest'] == 3:
                        json_trash['Status'] = 'FAIL'  
            
            ''' Handle the linked tickets '''
            liste = list()
            if len(val['issuelinks']) > 0:
                for i in range(len(val['issuelinks'])):
                    try:
                        liste.append((val['issuelinks'][i]['inwardIssue']['key'], self.cfg.BASE_URL + val['issuelinks'][i]['inwardIssue']['key']))
                    except KeyError:
                        pass
                    try:
                        liste.append((val['issuelinks'][i]['outwardIssue']['key'], self.cfg.BASE_URL + val['issuelinks'][i]['outwardIssue']['key']))
                    except KeyError:
                        pass
            
            for i in range(len(liste)):
                bug_key, bug_url = liste[i]
                try:
                    if len(liste) > 1:
                        jira_ticket = self.grab_linked_tickets(liste)
                        issuetype = jira_ticket[bug_key]['issuetype']['name']
                        if issuetype == 'Bug':
                            json_trash['Bug_'+str(i+1)+'_summary'] = jira_ticket[bug_key]['summary']
                            json_trash['Bug_'+str(i+1)+'_url'] = self.base_url + bug_key
                    else:
                        jira_ticket = self.consult_url(bug_url).json()                    
                        issuetype = jira_ticket['fields']['issuetype']['name']
                        if issuetype == 'Bug':
                            json_trash['Bug_'+str(i+1)+'_summary'] = jira_ticket['fields']['summary']
                            json_trash['Bug_'+str(i+1)+'_url'] = self.base_url + bug_key
                except ConnectionError as e:
                    if self.verbose is True:
                        print(e)
                    logging.getLogger(__name__).error(f'Connection Error when consulting links of the ticket: {e}')
                    raise
                except TypeError as e: # add to TEST
                    if self.verbose is True:
                        print(e)
                    logging.getLogger(__name__).error(f'Could not serialize the payload: {e}')
                    raise

            final_json[jira_key] = json_trash
        return final_json

def main(name):
    ''' Instantiate the Extractor class, grab the tickets from the JIRA API and output an excel '''
    ''' Objective: have an excel that gathers test steps, text execution and bugs into a nice readable record '''
    ''' Xray provides a nice GUI but the reporting does not suit the needs of the project management hence this report '''
    extractor = TestExtractor(name = name)
    
    if extractor.runtests is True:
        extractor.run_tests()
    
    extractor.startTimer
    json = extractor.grab_tickets(dict())
    json = extractor.remove_custom_fields(json, 'customfield_17284', 'customfield_17290')
    json = extractor.clean_json(json)
    extractor.generate_excel(json)
    extractor.closeTimer

def test_fixtures(NAME):
    VERBOSE = False
    return TestExtractor(name = NAME, verbose = VERBOSE)

if __name__ == "__main__":
    main(NAME)

