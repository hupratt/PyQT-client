import requests, time, re, logging, os
import pandas as pd
from base_class import BaseExtractor
from decorator_base import Memorize
from utils import MyDefaultDict
from json import JSONDecodeError

NAME = 'JIRA'


class LogExtractor(BaseExtractor):
    
    def __init__(self, name: str, verbose = None) -> None:
        super().__init__(name = name, verbose = verbose) 
        ''' constants '''
        self.URL = self.yml['jira']['URL_1'] + self.yml['jira']['JQL'] + str(self.yml['jira']['URL_2'])
        self.search = self.URL + self.yml['jira']['LINK'] + str(self.yml['jira']['START_AT'])
        
    def generate_excel(self, dictionary: dict) -> None:
        ''' Generate an excel from the dictionary provided in the input section '''
        ''' Transform certain columns into datetime objects so that excel can sort them properly ''' 
        timerz=time.strftime("%Y%m%d_%H%M%S_"+str(len(dictionary)))
        filename = str(self.name)+'_'+timerz+'.xlsx'
        df = pd.DataFrame.from_dict(dictionary,orient='index')
        
        date_headers = ['lastViewed', 'resolutiondate', 'updated', 'duedate', 'created']
        for i in date_headers:
            df[i] = pd.to_datetime(df[i], format="%Y/%m/%d", errors='ignore')
            
        writer = pd.ExcelWriter(filename, engine='xlsxwriter', options={'remove_timezone': True})
        df.to_excel(writer, sheet_name='LEO and MISC', header=True, index=True)
        
        ''' Close the Pandas Excel writer and output the Excel file '''
        self.save_excel(writer)
        self.test_file_creation

    @Memorize(func_name = "grab_tickets", file_name = os.path.basename(__file__))
    def grab_tickets(self, dictionary: dict) -> dict:
        return super().grab_tickets(dictionary) 

#    @Memorize(func_name = "clean_json", file_name = os.path.basename(__file__))
    def clean_json(self, dictionary) -> dict:
        ''' Mapping function '''
        ''' Go through the json and pick the right values to add to the excel ''' 
        '''
        # Business Analyst: customfield_12383
        # Business Representative: customfield_10100
        # PSP: customfield_12706
        '''
        final_json = dict()
        for jira_key, val in dictionary.items():
            json_trash = dict()
            ''' 
            Use default dict so that KeyError exceptions dont need to be wrapped around every mapping function, also if val is not a dictionary it is simply ignored
            Using a custom default dict to customize the class' __repr__ dunder method
            '''
            val_ = MyDefaultDict(val)
            val = val_
            
            ''' Grab watchers: this next loop takes a while to get done ~ 4 minutes '''
            if val["watches"]['watchCount'] > 0:
                try:
                    ''' no risk of denial of service because 1 request per ticket maximum '''
                    value = requests.get(val['watches']['self'], headers = {"Authorization": "Basic %s" % self.cfg.u, "Content-Type": "application/json"}, verify = False).json()
                except ConnectionError as e:
                    if self.verbose is True:
                        print(e)
                    logging.getLogger(__name__).error(f'Could not fetch watches URL: {e}')
                    raise
                except TypeError as e: # add to TEST
                    if self.verbose is True:
                        print(e)
                    logging.getLogger(__name__).error(f'Could not serialize the payload: {e}')
                    raise
                    
                watchers = value['watchers']
                _liste = [watcher['emailAddress'] for watcher in watchers if len(watcher) > 0]
                json_trash['watches'] = _liste
            
            ''' Versions '''
            if len(val['versions']) > 0 and val['versions'][0]['name'] is not None:
                json_trash['versions'] = val['versions'][0]['name']

            ''' PSP '''
            if len(val['customfield_12706']) > 0:
                json_trash['PSP'] = val['customfield_12706'][0]

            ''' fixVersions '''
            if len(val['fixVersions']) > 0:
                try:
                    json_trash['fixVersions'] = val['fixVersions'][0]['name']
                except KeyError:
                    logging.getLogger(__name__).error("fixVersions exception logged")
                    raise
            
            ''' Issue links ''' 
            issuelinks = list()
            if len(val['issuelinks']) > 0:
                for i in range(len(val['issuelinks'])):
                    try:
                        issuelinks.append(val['issuelinks'][i]['inwardIssue']['key'])
                    except KeyError:
                        issuelinks.append(val['issuelinks'][i]['outwardIssue']['key'])
                json_trash['issuelinks'] = issuelinks
            
            ''' Subtasks '''
            subtasks = list()
            if len(val['subtasks']) > 0:
                for i in range(len(val['subtasks'])):
                    try:
                        subtasks.append(val['subtasks'][i]['key'])
                    except KeyError:
                        logging.getLogger(__name__).error("subtasks exception logged")
                        raise
                json_trash['subtasks'] = subtasks
            
            ''' Lables'''
            if len(val['labels']) > 0:
                json_trash['labels'] = val['labels']
            
            ''' Priority '''
            if val['priority'] is not None:
                json_trash['priority'] = val['priority']['name']

            ''' Resolution '''
            if val['resolution'] is not None:
                json_trash['resolution'] = val['resolution']['name']
            
            ''' Description '''
            if val['description'] is not None:
                json_trash['description'] = re.sub('\{[^(aeiu)]*\}', '', str(val['description']))
            
            ''' Environment '''
            if val['environment'] is not None:
                json_trash['environment'] = val['environment']

            ''' Business Representative '''
            if val['customfield_10100'] is not None:
                json_trash['Business Representative'] = val['customfield_10100']['emailAddress']
            
            ''' Business Analyst '''
            if val['customfield_12383'] is not None:
                json_trash['Business Analyst'] = val['customfield_12383'][0]['emailAddress']
            
            ''' Assignee '''
            if val['assignee'] is not None:
                json_trash['assignee'] = val['assignee']['displayName']
            
            ''' Aggregateprogress '''
            if 'percent' in val['aggregateprogress']:
                json_trash['aggregateprogress'] = val['aggregateprogress']['percent']
            
            ''' Progress '''
            if 'percent' in val['progress']:
                json_trash['progress'] = val['progress']['percent']
            
            json_trash['summary'] = val['summary']
            json_trash['resolutiondate'] = val['resolutiondate']
            json_trash['updated'] = val['updated']
            json_trash['timeoriginalestimate'] = val['timeoriginalestimate']
            json_trash['aggregatetimeoriginalestimate'] = val['aggregatetimeoriginalestimate']
            json_trash['lastViewed'] = val['lastViewed']
            json_trash['duedate'] = val['duedate']
            json_trash['timeestimate'] = val['timeestimate']
            json_trash['aggregatetimeestimate'] = val['aggregatetimeestimate']
            json_trash['timespent'] = val['timespent']
            json_trash['parent'] = val['parent']['key']
            json_trash['aggregatetimespent'] = val['aggregatetimespent']
            json_trash['reporter'] = val['reporter']['displayName']
            json_trash['workratio'] = val['workratio']
            json_trash['created'] = val['created']
            json_trash['votes'] = val['votes']['votes']
            json_trash['issuetype'] = val['issuetype']['name']
            json_trash['project'] = val['project']['name']
            json_trash['creator'] = val['creator']['displayName']
            json_trash['status'] = val['status']['name']

            final_json[jira_key] = json_trash
            
        return final_json

def main(name):
    ''' Instantiate the Extractor class, grab the tickets from the JIRA API and output an excel '''
    ''' This script logs specific JIRA fields from projects in Luxembourg to an excel so that we can: '''
    ''' 1.	build reporting around the tool’s utilization '''
    ''' 2.	run data quality checks '''
    ''' 3.	be able to roll-back to a certain state '''
    extractor = LogExtractor(name = name)

    if extractor.runtests is True:
        extractor.run_tests()
    
    extractor.startTimer        
    json = extractor.grab_tickets(dict())
    json = extractor.remove_custom_fields(json, 'customfield_12383', 'customfield_10100', 'customfield_12706')
    json = extractor.clean_json(json)
    extractor.generate_excel(json)
    extractor.closeTimer

def test_fixtures(NAME) -> LogExtractor:
    VERBOSE = False
    return LogExtractor(name = NAME, verbose = VERBOSE)


if __name__ == "__main__":
    main(NAME)

