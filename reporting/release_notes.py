import time, re, argparse, os
import pandas as pd
from base_class import BaseExtractor
from pandas import DataFrame
from datetime import datetime
import img.RESOURCES as RESOURCES
from decorator_base import Memorize

NAME = 'JIRA_Release_Notes'

class ReleaseNoteExtractor(BaseExtractor):
    
    def __init__(self, name: str, verbose = None) -> None:
        super().__init__(name = name, verbose = verbose) 
        ''' These parameters can be overriden by CLI parameters with load_argparser() '''
        self.system = self.yml['release']['SYSTEM']
        self.deploy_date = self.yml['release']['DEPLOY_DATE']
        self.release_version = self.yml['release']['RELEASE_VERSION']
        ''' constants '''
        self.URL = self.yml['release']['URL_1'] + str(self.release_version) + self.yml['release']['URL_2']
        self.search = self.URL + self.yml['jira']['LINK'] + str(self.yml['jira']['START_AT'])
        
    def generate_argparser(self) -> argparse.ArgumentParser:
        parser = super().generate_argparser()
        parser.add_argument('-r','--release', choices=['19.07.EU '], help = 'specify a release version in JIRA', required=True)
        parser.add_argument('-sys', '--system', choices=['T24', 'TAP'], help = 'specify the impacted system, this only has impact on the email template', required=True)
        parser.add_argument('-d', '--deploydate', help = 'specify the deploy date, this only has impact on the email template', required=True)
        return parser

    def generate_excel(self, dictionary: dict) -> None: 
        ''' Generate an excel from the dictionary provided in the input section '''
        ''' Transform certain columns into datetime objects so that excel can sort them properly ''' 
        timerz=time.strftime("%Y%m%d_%H%M%S_"+str(len(dictionary)))
        filename = str(self.name)+'_'+timerz+'.xlsx'
        df = pd.DataFrame.from_dict(dictionary,orient='index')
        writer = pd.ExcelWriter(filename, engine='xlsxwriter', options={'remove_timezone': True})
        df.to_excel(writer, sheet_name=self.release_version, header=True, index=True)
        
        ''' Close the Pandas Excel writer and output the Excel file '''
        self.save_excel(writer)
        self.test_file_creation
    
    @Memorize(func_name = "grab_tickets", file_name = os.path.basename(__file__))
    def grab_tickets(self, dictionary: dict) -> dict:
        return super().grab_tickets(dictionary) 
    
    def clean_json(self, dictionary: dict) -> DataFrame:
        ''' Mapping function '''
        ''' Go through the json and pick the right values to add to the excel ''' 
        ''' Steps: customfield_17284 '''
        ''' Xray status: customfield_17290 '''
        final_json = dict()
        for jira_key, val in dictionary.items():
            json_trash = dict()
            json_trash['Issue Type'] = val['issuetype']['name']
            json_trash['Summary'] = val['summary']
            json_trash['Status'] = val['status']['name']
            json_trash['Description'] = val['description']
            json_trash['Reporter'] = val['reporter']['displayName']
            if val['assignee'] is not None:
                json_trash['Assignee'] = val['assignee']['displayName']
            
            if len(val['customfield_12706']) > 0:
                json_trash['PSP'] = val['customfield_12706'][0]
            
            final_json[jira_key] = json_trash
        return final_json

    def generate_email(self, dictionary: dict) -> None:
        ''' Generate a .html that can later be attached as an email '''
        DATE_TOP_LEFT = datetime.now()

        HEAD = RESOURCES.HEAD
        HEAD += str(DATE_TOP_LEFT.strftime('%d.%m.%Y'))

        HEAD += RESOURCES.SUB_HEAD
        HEAD += '{} Release {} {}'.format(self.system, DATE_TOP_LEFT.strftime('%B %Y'), self.release_version)
        HEAD += RESOURCES.SUB_HEAD_2
        
        SUBJECT = "SUBJECT: {} Freeze notification".format(self.system)
        HEAD += SUBJECT
        HEAD += RESOURCES.SUB_HEAD_2_1
        HEAD += RESOURCES.SUB_HEAD_2_2
        
        HEAD += """The {} tickets outlined below will be deployed on the 
        weekend of the {}. Please note that no further deployment requests
        will be accepted. """.format(str(len(dictionary)), self.deploy_date)
        
        HEAD += RESOURCES.SUB_HEAD_3
        HEAD += RESOURCES.TABLE_1
        for key, val in dictionary.items():
            if val['Issue Type']== "Bug":
                HEAD += RESOURCES.OBJ_1_BUG
            elif val['Issue Type'] == "New Feature":
                HEAD += RESOURCES.OBJ_1_FEAT
            elif val['Issue Type'] == "Task":
                HEAD += RESOURCES.OBJ_1_TSK
            elif val['Issue Type'] == "Change Request":
                HEAD += RESOURCES.OBJ_1_CR
            elif val['Issue Type'] == "Story":
                HEAD += RESOURCES.OBJ_1_STR
            elif val['Issue Type'] == "Requirement":
                HEAD += RESOURCES.OBJ_1_REQ
            elif val['Issue Type'] == "Epic":
                HEAD += RESOURCES.OBJ_1_EPC
            else:
                HEAD += RESOURCES.OBJ_1
            LINK = "https://jira.com/browse/"+str(key)
            HEAD += LINK
            HEAD += RESOURCES.OBJ_2
            HEAD += str(key)
         
            HEAD += RESOURCES.OBJ_3
            summary = val['Summary']
            HEAD += summary
            HEAD += RESOURCES.OBJ_4
            description = val['Description']
            new_description = re.sub('\{[^(aeiu)]*\}', '', description)
            description_paragraph = new_description
            HEAD += description_paragraph
            
            HEAD += RESOURCES.OBJ_5        
            
#            HEAD += RESOURCES.OBJ_6
#            HEAD += "Bullet point example 1"
#            HEAD += RESOURCES.OBJ_7
#            HEAD += RESOURCES.OBJ_6
#            HEAD += "Bullet point example 2"
#            HEAD += RESOURCES.OBJ_7
            
        HEAD += RESOURCES.TABLE_2
        with open(self.name+str('.html'), 'w') as file:
            file.write(HEAD)
            
def main(name):
    ''' Instantiate the Extractor class, grab the tickets from the JIRA API and output an .html '''
    ''' Confluence and JIRA provide a nice interface for the management of each release but there is no good looking email builder interface '''
    ''' This report fills this need '''
    extractor = ReleaseNoteExtractor(name = NAME)
    if extractor.runtests is True:
        extractor.run_tests()
    
    extractor.startTimer
    json = extractor.grab_tickets(dict())
    json = extractor.remove_custom_fields(json, 'customfield_12706')
    print(json)
    json = extractor.clean_json(json)
    extractor.generate_excel(json)
    extractor.generate_email(json)
    extractor.closeTimer

def test_fixtures(NAME):
    VERBOSE = False
    return ReleaseNoteExtractor(name = NAME, verbose = VERBOSE)
    
if __name__ == "__main__":
    main(NAME)

