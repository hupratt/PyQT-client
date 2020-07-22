from typing import Callable
import os, yaml
import logging, time
from timeit import default_timer as timer
from collections import defaultdict


class Loader:
    @staticmethod
    def cache_exists(liste) -> bool:
        _directory = [i for i in os.listdir(os.path.curdir)]
        for element in liste:
            a, b = element
            for file in _directory: 
                if (file.startswith(a) and file.endswith(b)):
                    return True
            return False
    @staticmethod
    def grab_configuration() -> Callable:
        curdir = os.getcwd()
        path = 'C:\\Users\\u46022\\Documents'
        os.chdir(path)
        import configuration
        os.chdir(curdir)
        return configuration
    def load_yml(self):
        with open(os.path.join(self.wdirectory, "config.yml"), 'r') as ymlfile:
            cfg = yaml.load(ymlfile, yaml.SafeLoader)
        return cfg

class MyLogger:
    @staticmethod
    def setLogger() -> logging.Logger:
        ''' check if FileHandler exists'''
        ''' FileHandler is created at python level and not @ the level of this class '''
        if len(logging.getLogger(__name__).handlers) == 0:
            ''' Instantiate the FileHandler aka logger object so that it records general info and exceptions into a .log file '''
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)
            ''' create a file handler '''
            handler = logging.FileHandler('jira_extract.log')
            handler.setLevel(logging.INFO)
            ''' create a logging format '''
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            ''' add the handlers to the logger '''
            logger.addHandler(handler)
            return logger
    @property
    def startTimer(self) -> None:
        ''' Start the timewatch '''
        logging.getLogger(__name__).info(f"Timer started for job: {self}")
        if self.verbose is True:
            print("Timer started @ "+time.strftime("%H:%M"))
    @property
    def closeTimer(self) -> None:
        ''' Stop the timewatch '''
        self.end = timer()
        elapsed = round((self.end-self.start)/60)
        stats = self.stats(elapsed)
        logging.getLogger(__name__).info(stats)
        if self.verbose is True:
            print(stats)

class MyDefaultDict(defaultdict):
    """
    Usage: 
    _json = {'fixVersions': {'customfield_14791': None}]}
    someddict = mydefaultdict(_json)
    print(someddict['fixVersions'])
    >> {'customfield_14791': None}
    print(someddict['customfield_14791'])
    >> None
    print(someddict['customfield_14791']['customfield_14791'])
    >> None
    print(someddict['fixVersions']['customfield_14792'])
    KeyError: 'customfield_14792'
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(MyDefaultDict, *args, **kwargs)
    def __repr__(self):
        return repr(self.dictify())
    def dictify(self):
        '''Get a standard dictionary of the items in the tree.
        
        d = dict()
        for k, v in self.items():
            if isinstance(v, dict) :
                d[k] = v.dictify()
            else:
                d[k] = v
        '''
        dictionary = dict((k, (v.dictify() if isinstance(v, dict) else v)) for k, v in self.items())
        if len(dictionary) > 0:
            return dictionary
