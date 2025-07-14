import logging.handlers
import dirtyjson, logging, os, sys, datetime, json, queue, uuid, time
from typing import Dict, List, cast, Any, Union, Optional

def GenerateUUID() -> str:
    """
    Generate a unique identifier string consisting of a UUID and the current time as a string.

    Returns:
        str: A string containing a UUID4 and the current time, separated by a dash.
    """
    return str(uuid.uuid4()) + f"-{int(time.time())}"


def GetWithDefault(d: dict, key, default = None):
    """Get a value associated with a key in a dictionary, or a default value if there's no key matched."""
    return d[key] if key in d else default

def SaferJsonObjectParse(raw_json: str, bound_check: bool = False) -> Dict[str, object]:
    """A safer Json Object parse, with can ignore some typos and error.

    Args:
        raw_json (str): The raw JSON string.
        bound_check (bool, optional): If this true, will clip and assumed the Json begin at the first '{' and end at the last '}'. Defaults to False.

    Returns:
        Dict[str, object]: The result parsed dict of the Json.
    """    
    #* To made AttributedDict to dict, recursively.
    def dict_from_attributed(obj):
        if isinstance(obj, dict):
            return {k: dict_from_attributed(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [dict_from_attributed(i) for i in obj]
        else:
            return obj
    
    curr_json = raw_json[raw_json.index('{'):raw_json.rindex('}') + 1] if bound_check else raw_json
    res = dirtyjson.loads(curr_json, encoding='utf-8')
    return cast(Dict[str, object], dict_from_attributed(res))

def GetQueryDictByPath(d: Dict[str, Any], path: str, path_sep='.', default: Any = None) -> Any:
    """Get a nested json element by a path. Notice that key is strictly a string.\n
    GetQueryDictByPath(d, 'a.sub_a') = d['a']['sub_a'] (or default=None if not exists).\n
    GetQueryDictByPath(d, '') = d(empty path)
    """
    if not path_sep:
        raise ValueError("The path seperator length must be >0!")
    
    steps: List[str] = path.split(path_sep)
    trace_steps: List[str] = []
    curr: Union[Dict[str, Any], Any] = d
    for step in steps:
        if not isinstance(curr, dict):
            raise ValueError(f"The path \"{path_sep.join(trace_steps)}\" is not points to a dictionary!")
        if step not in curr:
            return default
        trace_steps.append(step)
        curr = curr[step]
    return curr

def SetQueryDictByPath(d: Dict[str, Any], path: str, value: Any, path_sep='.') -> bool:
    """Set a nested json element by a path. Notice that key is strictly a string.\n
    SetQueryDictByPath(d, 'a.sub_a', 3) => d['a']['sub_a'] = 3 (or return False if not exists).\n
    SetQueryDictByPath(d, '', {}) => return False (since can't set global).
    """
    if not path_sep:
        raise ValueError("The path seperator length must be >0!")
    
    steps: List[str] = path.split(path_sep)
    trace_steps: List[str] = []
    curr: Union[Dict[str, Any], Any] = d
    last: Optional[Dict[str, Any]] = None
    for step in steps:
        if not isinstance(curr, dict):
            raise ValueError(f"The path \"{path_sep.join(trace_steps)}\" is not points to a dictionary!")
        if step not in curr:
            return False
        trace_steps.append(step)
        
        last, curr = curr, curr[step]

    if last:
        last[steps[-1]] = value
        return True
    else:
        return False
    

class Logger:
    """The Logger class, use for logging."""
    __logger: Optional[logging.Logger] = None
    
    __log_queue: Optional[queue.Queue] = None
    __queue_handler: Optional[logging.handlers.QueueHandler] = None
    __queue_listener: Optional[logging.handlers.QueueListener] = None    
    
    @staticmethod
    def Initialize():
        """Initialize the Logger."""
        formatter = logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s: %(message)s",
                                        datefmt="%d-%m-%Y %H:%M:%S")
        
        dir_name = os.path.join(os.getcwd(), Config.GetConfig("logging.file.folder", "logs"))
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        Logger.__log_queue = queue.Queue()
        Logger.__queue_handler = logging.handlers.QueueHandler(Logger.__log_queue)
        
        Logger.__queue_listener = logging.handlers.QueueListener(Logger.__log_queue, Logger.__queue_handler)
        Logger.__queue_listener.start()
        
        Logger.__logger = logging.Logger(Config.GetConfig("logging.name", "Logger"))
        Logger.__logger.addHandler(Logger.__queue_handler)
        
        if Config.GetConfig("logging.console.enabled", False):
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.DEBUG if Config.GetConfig("logging.console.debugMode", False) else logging.INFO)
            console_handler.setFormatter(formatter)
            Logger.__logger.addHandler(console_handler)
            
        if Config.GetConfig("logging.file.enabled", False):
            curr_time = datetime.datetime.now(datetime.UTC)
            file_name = curr_time.strftime(Config.GetConfig("logging.file.nameFormat", "%Y%m%d-%H%M%S.log"))
            
            file_handler = logging.FileHandler(os.path.join(dir_name, file_name), encoding='utf-8')
            file_handler.setLevel(logging.DEBUG if Config.GetConfig("logging.file.debugMode", False) else logging.INFO)
            file_handler.setFormatter(formatter)
            Logger.__logger.addHandler(file_handler)
        
    @staticmethod
    def LogDebug(msg: str):
        """Log a Debug message."""
        if Logger.__logger:
            Logger.__logger.debug(msg)

    @staticmethod
    def LogInfo(msg: str):
        """Log an Informative message."""
        if Logger.__logger:
            Logger.__logger.info(msg)

    @staticmethod
    def LogWarning(msg: str):
        """Log a Warning message."""
        if Logger.__logger:
            Logger.__logger.warning(msg)

    @staticmethod
    def LogError(msg: str):
        """Log an Error message."""
        if Logger.__logger:
            Logger.__logger.error(msg)

    @staticmethod
    def LogException(ex: Exception, msg: Optional[str] = None):
        """Log an Exception with the messages."""
        if Logger.__logger:
            exception_type = type(ex).__name__
            exception_message = f"{msg + ' - ' if msg else ''}{exception_type}: {str(ex)}"
            Logger.__logger.error(exception_message)


class Config:
    """The Config class, contain the static configuration of the application."""
    CONFIG_NAME_SEPERATOR = '.'
    """The seperator between config and sub-config name (ex: logging.name -> The 'name' options of the 'logging' category)."""
    CONFIG_FILE_PATH = os.path.join('data', 'configs', 'general.json')
    """The path of the global config file."""
    
    __data: Dict[str, object] = {}
    
    @staticmethod
    def Initialize() -> bool:
        """Initialize the Config class by loading from a config file."""
        try:
            with open(Config.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                Config.__data = SaferJsonObjectParse(f.read())
            return True
        except Exception:
            return False
        
    @staticmethod
    def SaveConfig() -> bool:
        """Save the current Config to the config file. Will not save if not initialized."""
        if not Config.__data or isinstance(Config.__data, dict):
            return False
        try:
            with open(Config.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(Config.__data, f)
            return True
        except Exception as e:
            Logger.LogException(e, "Config: Failed to save config")
            return False
    
    @staticmethod
    def GetConfig(config_name: str, default=None) -> Any:
        """Get the config value from the given config name, or return a default value if not match.\n
        Seperate by '.' for subconfig (e.g. ex_config.ex_sub_config)"""
        if not Config.__data:
            raise Exception("The Config didn't initialized!")
        return GetQueryDictByPath(Config.__data, config_name, Config.CONFIG_NAME_SEPERATOR, default)