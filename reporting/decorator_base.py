import functools
import pickle
import inspect
import os, time
import re
import unicodedata
from pandas import DataFrame

class Debug:
    '''
    When a child method is decorated with this class then this class
    prints out the signature (method name and arguments) 
    as well as the output of the method in the command line
    '''

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs): 
        args_repr = [repr(a) for a in args]                      
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  
        signature = ", ".join(args_repr + kwargs_repr)           
        print(f"Calling {self.func.__name__}({(signature)})")
        value = self.func(self, *args, **kwargs)
        print(f"{self.func.__name__} returned {(value)}")           
        return value

class Memorize:
    ''' 
    Memorize checks whether a clean json pickle exists in cache. 
    If the arguments to the function are the same then the pickle is loaded and the function is bypassed 
    (ie. the function is not reevaluated)
    Otherwise the function is loaded and a pickle is saved in a .cache file. 
    The filename is passed to clean json so that it can be used in the naming of the pickle file. 
    This ensures the unicity of the pickle file accross reports
    fork: https://github.com/brmscheiner/memorize.py
    '''
    def __init__(self, file_name="unknown file", func_name="unknown function"):
        self.file_name = file_name
        self.func_name = func_name
        self.set_cache_filename
        self.set_parent_file

    def __call__(self, func, *args):
        def wrapper(*args):
            params = list()
            for arg in args:
                if isinstance(arg, (dict, list, DataFrame)):
                    params.append(arg)
                    if self.cache_exists():
                        self.read_cache()
                        if self.params == params:
                            print(f"Reading cache of function: {self.func_name} from {self.file_name}")
                            return self.cache
            self.save_params(params)
            self.cache = func(*args)
            self.save_cache
            return self.cache
        return wrapper

    @property
    def set_parent_file(self):
        """
        Sets self.parent_file to the absolute path of the
        file containing the memoized function.
        """
        rel_parent_file = inspect.stack()[-1].filename
        self.parent_filepath = os.path.abspath(rel_parent_file)
        
    @property
    def set_cache_filename(self):
        """
        Sets self.cache_filename to an os-compliant
        version of "file_function.cache"
        """
        file_name = _slugify(self.file_name.replace('.py', ''))
        func_name = _slugify(self.func_name)
        timerz = time.strftime("%Y%m%d")
        self.cache_filename = file_name + '_' + func_name + '_' + timerz + '.cache'

    def get_last_update(self):
        """
        Returns the time that the parent file was last
        updated.
        """
        last_update = os.path.getmtime(self.parent_filepath)
        return last_update

    def read_cache(self):
        """
        Read a pickled dictionary into self.timestamp and
        self.cache. See self.save_cache.
        """
        with open(self.cache_filename, 'rb') as f:
            data = pickle.loads(f.read())
            self.timestamp = data['timestamp']
            self.params = data['params']
            self.cache = data['cache']

    def save_params(self, params):
        """
        Separating the save cache from the save params is an inevitable workaround 
        because calling the decorated function func(*args) 
        somehow messes up the parameter variable in the __call__ method
        """
        with open(self.cache_filename, 'wb+') as f:
            out = dict()
            out['params'] = params
            f.write(pickle.dumps(out))
    
    @property
    def save_cache(self):
        """
        Pickle the file's timestamp and the function's cache
        in a dictionary object.
        """
        out = open(self.cache_filename, 'rb')
        out = pickle.loads(out.read())
        with open(self.cache_filename, 'wb+') as f:
            out['timestamp'] = self.get_last_update()
            out['cache'] = self.cache
            f.write(pickle.dumps(out))
        
    def cache_exists(self):     
        '''
        Returns True if a matching cache exists in the current directory.
        '''
        if os.path.isfile(self.cache_filename):
            return True
        return False


    def __get__(self, obj, objtype):
        """ Support instance methods. """
        return functools.partial(self.__call__, obj)

def _slugify(value):
    """
    Normalizes string, converts to lowercase, removes
    non-alpha characters, and converts spaces to
    hyphens. From
    http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub(r'[^\w\s-]', '', value.decode('utf-8', 'ignore'))
    value = value.strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value

def _filename_from_path(filepath):
    return filepath.split('/')[-1]

