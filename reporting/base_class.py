import requests, math, os, time
from timeit import default_timer as timer
import unittest
from typing import Callable
from pandas import ExcelWriter
from requests.models import Response
import argparse, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import Loader, MyLogger



class BaseExtractor(Loader, MyLogger):
    ''' Base class for our extractors. '''
    ''' Without it a lot of utility functions would be repeated accross classes. '''
    def __init__(self, name: str, verbose = None) -> None:
        
        self.start = timer()
        self.end = 0
        self.wdirectory = os.path.dirname(os.path.abspath(__file__))
        self.name = name
        self.log = self.setLogger()
        self.yml = self.load_yml()
        ''' yml parameters can be overriden by CLI parameters with load_argparser() '''
        self.credentials = self.yml['jira']['CREDENTIALS']
        if verbose is None:
            self.verbose = self.yml['jira']['VERBOSE']
        else:
            self.verbose = verbose
        self.runtests = self.yml['jira']['RUN_UNIT_TEST']
        ''' if args are specified through the CLI then load_argparser is triggered '''
        self.load_argparser()
        self.cfg = self.retrieve_credentials(self.credentials)

    def __repr__(self) -> str:
        ''' Called when instance is called directly '''
        return self.name
    
    def __setattr__(self, name, val) -> object:
        ''' Called when class attributes are updated '''
        # print(f"Setting attribute {name} to {val}")
        return object.__setattr__(self, name, val)
    
    def __getattribute__(self, name) -> object:
        ''' Called when class attributes are called '''
        # print(f"Class attribute called: {name}")
        return object.__getattribute__(self, name)

    def __get__(self, obj, objtype) -> object:
        ''' Called when instance attributes are called '''
        print('Retrieving instance var', self.name)
        return self.val

    def __set__(self, obj, val) -> None:
        ''' Called when instance attributes are updated '''
        print('Updating instance var', self.name)
        self.val = val

    def stats(self, elapsed) -> str:
        return f"{self} done in ~ {elapsed} minutes"

    def generate_excel(self, dictionary: dict) -> Exception:
        raise NotImplementedError("Subclass must implement abstract method")
        
    def clean_json(self, dictionary: dict) -> Exception:
        raise NotImplementedError("Subclass must implement abstract method")

    @staticmethod
    def generate_argparser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Add option parameters to control the execution of the script')
        parser.add_argument('-v', '--verbose', action = 'store_true', help = 'enable print statements', default=False)
        parser.add_argument('-test', '--runtests', action = 'store_true', help = 'run unit tests before script execution', default=False)
        parser.add_argument('-cred', '--credentials', help = 'specify the path with your JIRA user and password', required=True)
        return parser
    
    def load_argparser(self) -> None:
        ''' if args are specified through the CLI then load_argparser is triggered '''
        if len(sys.argv) > 1:
            parser = self.generate_argparser()
            args = parser.parse_args()
            ''' override hard coded params with CLI params '''
            self.verbose = args.verbose
            self.runtests = args.runtests
            self.credentials = args.credentials
            try:
                self.release_version = args.release
                self.system = args.system
                self.deploy_date = args.deploydate
            except AttributeError:
                pass
            try:
                self.psp = args.psp
                self.system = args.environment
            except AttributeError:
                pass        
    
    @staticmethod
    def run_tests() -> None: 
        import custom_test
        suite = unittest.TestLoader().loadTestsFromModule(custom_test)
        unittest.TextTestRunner(verbosity=2).run(suite)

    def wrapper(self, url, dictionary) -> dict:
        response = self.consult_url(url).json()
        return self.list_to_json(response['issues'], dictionary)
            
    def consult_url(self, url: str) -> Response:
        ''' Consult the API and return the field values of 1000 tickets at a time (maximum value)'''
        return requests.get(url, headers = {"Authorization": "Basic %s" % self.cfg.u, "Content-Type": "application/json"}, verify = False)

    def list_to_json(self, liste: list, dictionary: dict) -> dict:
        ''' Feed the dictionary with the newly grabbed list of dictionaries from the API '''
        for ticket in liste:
            dictionary[ticket['key']] = ticket['fields']
        if self.verbose is True:
            print(str(len(dictionary))+' retrieved so far')
        return dictionary

    def number_iter_counter(self) -> int:
        response = self.consult_url(self.search).json()
        return math.ceil(response['total'] / 1000)

    def url_builder(self) -> list:
        urls = list()
        for _ in range(self.number_iter_counter()):
            urls.append(self.search)
            self.yml['jira']['START_AT'] += 1000
            self.search = self.URL + self.yml['jira']['LINK'] + str(self.yml['jira']['START_AT'])
        return urls
    
    def grab_tickets(self, dictionary: dict) -> dict:
        ''' Fire individual threads that consult the API, return the field values of 1000 tickets each and return the consolidated dictionary '''
        processes, json = list(), dict()
        with ThreadPoolExecutor(max_workers=10) as executor:
            for url in self.url_builder():
                # Schedules the callable: wrapper to be executed and returns a Future object representing the execution of the callable.
                processes.append(executor.submit(self.wrapper, url, dictionary))                
        for task in as_completed(processes):
            json.update(task.result())
        return json

    def grab_linked_tickets(self, liste: list) -> dict:
        ''' grab linked tickets asynchronously '''
        processes, json = list(), dict()
        with ThreadPoolExecutor(max_workers=10) as executor:
            for url in liste:
                # Schedules the callable: wrapper to be executed and returns a Future object representing the execution of the callable.
                processes.append(executor.submit(self.consult_url, url))                
        for task in as_completed(processes):
            json.update(task.result().json())
        return json
    
    @staticmethod
    def remove_custom_fields(json: dict, *args) -> dict: 
        ''' All custom fields are removed except the ones passed in as parameters '''
        final_json = dict()
        for key, _ in json.items():
            main_fields_json = dict()
            for field in json[key].keys():
                for _arg in args:
                    if _arg in field:
                        main_fields_json[field] = json[key][field]
                    elif 'customfield' not in field:
                        main_fields_json[field] = json[key][field]
            final_json[key] = main_fields_json
        return final_json
    
    def retrieve_credentials(self, path: str) -> Callable: 
        ''' Return a callable module with my credentials '''
        if os.path.isfile(path):
            path = os.path.dirname(path)
        ''' By default, Python looks for its modules and packages in $PYTHONPATH '''
        sys.path.append(path)
        os.chdir(path)
        import configuration
        os.chdir(self.wdirectory)
        return configuration
    
    def save_excel(self, writer: ExcelWriter) -> None:
        ''' Save the previously generated excel '''
        if not os.path.exists(self.name):
            if self.verbose is True:
                print(f"Folder name '{self}' was created")
            os.makedirs(self.name)
            os.chdir(self.name)
        else:
            if self.verbose is True:
                print(f"Folder name '{self}' already exists")
            os.chdir(self.name)
        writer.save()

    @property
    def test_file_creation(self) -> None:
        os.chdir(os.path.join(self.wdirectory, self.name))
        timerz=time.strftime("%Y%m%d")
        filename = str(self.name)+'_'+timerz
        self.search_import_file(filename,".xlsx")
        os.chdir(self.wdirectory)
    
    def search_import_file(self, a, b) -> str:
        _directory = [i for i in os.listdir(os.path.curdir)]
        for file in _directory: 
            if (file.startswith(a) and file.endswith(b)):
                curdir = os.path.abspath(os.path.curdir)
                path_to_file = os.path.join(curdir,file)
                if self.verbose is True:
                    size = os.path.getsize(path_to_file)
                    print(f"[TEST OK] File was successfully created: {a} size: {size} bytes")
                    if size > 2e9:
                        print("[TEST FAIL] File is bigger than 2MB, something is wrong in the mapping function")
                    elif size < 100:
                        print("[TEST FAIL] File is too small, something just broke")
                return path_to_file, file
        raise ValueError("IO Error: No file was created")


