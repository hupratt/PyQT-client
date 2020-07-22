import unittest, time, os, logging, sys
from requests.models import Response
from random import randint
from requests.exceptions import Timeout, ConnectionError
from unittest.mock import patch, Mock, call
from functools import partial
from grab_tickets_json import grab_tickets_json
from contextlib import contextmanager
from utils import Loader
from json.decoder import JSONDecodeError


found_cache = partial(Loader.cache_exists,[(str('deployment_log_uat_grab_tickets_'+time.strftime("%Y%m%d")),".cache"),
                                    (str('deployment_log_uat_clean_json_'+time.strftime("%Y%m%d")),".cache"),
                                    (str('jira_routine_v2_grab_tickets_'+time.strftime("%Y%m%d")),".cache"),
                                    (str('jira_routine_v2_clean_json_'+time.strftime("%Y%m%d")),".cache")])


class BeforeProgramStartTests(unittest.TestCase, Loader):
    
    def __init__(self, *args) -> None:
        import test_extraction_V2
        import jira_routine_V2
        import release_notes
        import deployment_log_UAT
        import barros_request
        
        super().__init__(*args)
        
        self.wdirectory = os.path.dirname(os.path.abspath(__file__))
        self.yml = self.load_yml()
        self.test_url = self.yml['unittest']['TEST_URL']
        self.TEST_watcher_1 = self.yml['unittest']['TEST_watcher_1']
        self.TEST_watcher_2 = self.yml['unittest']['TEST_watcher_2']
        self.TEST_call_1 = self.yml['unittest']['TEST_call_1']
        self.TEST_call_2 = self.yml['unittest']['TEST_call_2']
        self.instances = [test_extraction_V2.test_fixtures(test_extraction_V2.NAME), 
                          jira_routine_V2.test_fixtures(jira_routine_V2.NAME), 
                          release_notes.test_fixtures(release_notes.NAME), 
                          deployment_log_UAT.test_fixtures(deployment_log_UAT.NAME),
                          barros_request.test_fixtures(barros_request.NAME)]
                
    def test_super_call(self) -> None:
        from base_class import BaseExtractor
        from barros_request import BarrosExtractor, NAME
        instance = BarrosExtractor(NAME, False)
        assert isinstance(instance, BaseExtractor) is True
        from test_extraction_V2 import TestExtractor, NAME
        instance = TestExtractor(NAME, False)
        assert isinstance(instance, BaseExtractor) is True
        from jira_routine_V2 import LogExtractor, NAME
        instance = LogExtractor(NAME, False)
        assert isinstance(instance, BaseExtractor) is True
        from release_notes import ReleaseNoteExtractor, NAME
        instance = ReleaseNoteExtractor(NAME, False)
        assert isinstance(instance, BaseExtractor) is True
        from deployment_log_UAT import DeployExtractor, NAME
        instance = DeployExtractor(NAME, False)
        assert isinstance(instance, BaseExtractor) is True
       
    @contextmanager
    def assertNotRaises(self, exc_type):
        try:
            yield None
        except exc_type:
            raise self.failureException(f'{exc_type.__name__} raised')

    def test_status_code_PROD(self) -> None:
        import release_notes
        inst = release_notes.test_fixtures(release_notes.NAME)
        response = inst.consult_url(self.test_url)
        if '4' in str(response.status_code)[0]:
            raise Exception("Password is probably wrong")
        if '5' in str(response.status_code)[0]:
            raise Exception("Check if JIRA is down or the URL is wrong")
        self.assertEqual(response.status_code, 200)

    def test_type_consult_url_PROD(self) -> None:
        import release_notes
        inst = release_notes.test_fixtures(release_notes.NAME)
        assert isinstance(inst.consult_url(self.test_url), Response)

    def test_list_to_json_PROD(self) -> None:
        import release_notes
        inst = release_notes.test_fixtures(release_notes.NAME)        
        response = inst.consult_url(self.test_url)
        list_of_dictionaries = response.json()['issues']
        assert isinstance(inst.list_to_json(list(), list_of_dictionaries[0]), dict)
        assert len(list_of_dictionaries[0]) > 0
        
    @unittest.skip # slow
    def test_grab_tickets_PROD(self) -> None:
        import release_notes
        inst = release_notes.test_fixtures(release_notes.NAME)
        grab = inst.grab_tickets(dict())
        assert isinstance(grab, dict)
        assert len(grab) > 0

    def test_status_code_UAT(self) -> None:
        import deployment_log_UAT
        inst = deployment_log_UAT.test_fixtures(deployment_log_UAT.NAME)
        response = inst.consult_url(self.test_url)
        if '4' in str(response.status_code)[0]:
            raise Exception("Password is probably wrong")
        if '5' in str(response.status_code)[0]:
            raise Exception("Check if JIRA is down or the URL is wrong")
        self.assertEqual(response.status_code, 200)

    def test_type_consult_url_UAT(self) -> None:
        import deployment_log_UAT
        inst = deployment_log_UAT.test_fixtures(deployment_log_UAT.NAME)
        assert isinstance(inst.consult_url(self.test_url), Response)

    def test_list_to_json_UAT(self) -> None:
        import deployment_log_UAT
        inst = deployment_log_UAT.test_fixtures(deployment_log_UAT.NAME)      
        response = inst.consult_url(self.test_url)
        list_of_dictionaries = response.json()['issues']
        assert isinstance(inst.list_to_json(list(), list_of_dictionaries[0]), dict)
        assert len(list_of_dictionaries[0]) > 0
        
    @unittest.skip # slow
    def test_grab_tickets_UAT(self) -> None:
        import deployment_log_UAT
        inst = deployment_log_UAT.test_fixtures(deployment_log_UAT.NAME)
        grab = inst.grab_tickets(dict())
        assert isinstance(grab, dict)
        assert len(grab) > 0

    def test_remove_custom_fields(self) -> None:
        inst = self.instances[randint(0,len(self.instances)-1)]
        assert isinstance(inst.remove_custom_fields(dict(), 'customfield_12706'), dict)

    def test_remove_custom_fields_signature_synthetic_data(self) -> None:
        grab_tickets_json = {'T2L-255': {'customfield_14791': None, 'customfield_14792': None, 'customfield_14795': None, 'customfield_14796': None}}
        from deployment_log_UAT import DeployExtractor, NAME
        inst = DeployExtractor(NAME, False)
        partial_function = partial(inst.remove_custom_fields, grab_tickets_json)
        assert len(partial_function('customfield_14791')['T2L-255']) == 1
        assert len(partial_function('customfield_14791','customfield_14792')['T2L-255']) == 2
        assert len(partial_function('customfield_14791','customfield_14792','customfield_14795')['T2L-255']) == 3
        assert len(partial_function('customfield_14791','customfield_14792','customfield_14795','customfield_14796')['T2L-255']) == 4
        assert partial_function('customfield_14791')['T2L-255'] == {'customfield_14791': None}

    def test_remove_custom_fields_signature_real_data(self) -> None:
        from deployment_log_UAT import DeployExtractor, NAME
        inst = DeployExtractor(NAME, False)
        dic = dict()
        dic['T2L-255'] = grab_tickets_json['T2L-255']
        partial_function = partial(inst.remove_custom_fields, dic)
        assert len(partial_function('resolution')['T2L-255']) == 33
        assert len(partial_function('aggregatetimeestimate','aggregateprogress','votes')['T2L-255']) == 33
        assert len(partial_function('customfield_12706')['T2L-255']) == 34

    def test_clean_json_lastViewed_exception_not_raised_when_not_present(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        if 'lastViewed' in grab_tickets_json['T2L-252'].keys():
            del grab_tickets_json['T2L-252']['lastViewed']
        # Limiting the size of the dictionary to avoid long processing times
        dic = dict()
        dic['T2L-252'] = grab_tickets_json['T2L-252']
        with self.assertNotRaises(KeyError):
            LogExtractor(NAME, False).clean_json(dic)      

    def test_clean_json_resolution_exports_correctly(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        # Limiting the size of the dictionary to avoid long processing times
        dic = dict()
        dic['T2L-255'] = grab_tickets_json['T2L-255']
        assert LogExtractor(NAME, False).clean_json(dic)['T2L-255']['resolution'] == 'Done'

    def test_clean_json_labels_exports_correctly(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        # Limiting the size of the dictionary to avoid long processing times
        dic = dict()
        dic['T2L-231'] = grab_tickets_json['T2L-231']
        assert LogExtractor(NAME, False).clean_json(dic)['T2L-231']['labels'] == grab_tickets_json['T2L-231']['labels']

    def test_clean_json_aggregatetimeoriginalestimate_exports_correctly(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        # Limiting the size of the dictionary to avoid long processing times
        dic = dict()
        dic['T2L-242'] = grab_tickets_json['T2L-242']
        assert LogExtractor(NAME, False).clean_json(dic)['T2L-242']['aggregatetimeoriginalestimate'] == grab_tickets_json['T2L-242']['aggregatetimeoriginalestimate']

    def test_clean_json_watches_exports_correctly(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        # Limiting the size of the dictionary to avoid long processing times
        dic = dict()
        dic['T2L-249'] = grab_tickets_json['T2L-249']
        assert LogExtractor(NAME, False).clean_json(dic)['T2L-249']['watches'] == self.TEST_watcher_1
        dic = dict()
        dic['T2L-12'] = grab_tickets_json['T2L-12']
        assert LogExtractor(NAME, False).clean_json(dic)['T2L-12']['watches'] == self.TEST_watcher_2
    
    def test_clean_json_fixVersions_KeyError(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        dic = {'T2L-249': {'watches': {'self': 'foo', 'watchCount': 0, 'isWatching': False},'fixVersions': [{'self': 'bar', 'id': '30453', 'name': '19.07.EU ', 'archived': False, 'released': False, 'releaseDate': '2019-07-21'}]}}
        del dic['T2L-249']['fixVersions'][0]['name']
        with self.assertRaises(KeyError):
            LogExtractor(NAME, False).clean_json(dic)

    def test_clean_json_fixVersions_KeyError_real_data(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        # Limiting the size of the dictionary to avoid long processing times
        dic = dict()
        dic['T2L-219'] = grab_tickets_json['T2L-219']
        del dic['T2L-219']['fixVersions'][0]['name']
        with self.assertRaises(KeyError):
            LogExtractor(NAME, False).clean_json(dic)
            
    def test_clean_json_subtasks_KeyError(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        dic = {'T2L-249': {'watches': {'self': 'foo', 'watchCount': 0, 'isWatching': False},'subtasks': [{'self': 'bar', 'key': '30453'}]}}
        del dic['T2L-249']['subtasks'][0]['key']
        with self.assertRaises(KeyError):
            LogExtractor(NAME, False).clean_json(dic)

    def test_generate_excel_LogExtractor(self) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        _json = {'T2L-249': {'resolutiondate': '2017-11-17T16:18:14.000+0100', 'updated': '2017-11-17T16:18:14.000+0100', 'duedate': '2017-11-17T16:18:14.000+0100', 'created': '2017-11-17T16:18:14.000+0100', 'lastViewed': '2019-08-23T11:27:38.820+0200'}}
        instance = LogExtractor(NAME, False)
        instance.generate_excel(_json)
        os.chdir(NAME)
        path, file = instance.search_import_file(NAME, "_1.xlsx")
        os.chdir(self.wdirectory)
        assert os.path.isfile(path) is True
        os.remove(path)
        
    def test_clean_json_execution_blocked_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17290': {'statuses': [{'statusResults':  [{'latest': 1000}]}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Status'] == 'BLOCKED'

    def test_clean_json_execution_pass_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17290': {'statuses': [{'statusResults':  [{'latest': 0}]}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Status'] == 'PASS'

    def test_clean_json_execution_executing_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17290': {'statuses': [{'statusResults':  [{'latest': 2}]}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Status'] == 'EXECUTING'
        
    def test_clean_json_execution_fail_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17290': {'statuses': [{'statusResults':  [{'latest': 3}]}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Status'] == 'FAIL'
        
    def test_clean_json_test_step_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17284': {'steps': [{'step': 'derp'}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Test step'] == 'derp'
        
    def test_clean_json_test_result_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17284': {'steps': [{'result': 'derp'}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Test result'] == 'derp'

    def test_clean_json_test_data_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'customfield_17284': {'steps': [{'data': 'derp'}]}}}
        instance = TestExtractor(NAME, False)
        _json = instance.clean_json(_json)
        assert _json['T2L-249']['Test data'] == 'derp'
        
    def test_generate_excel_TestExtractor(self) -> None:
        from test_extraction_V2 import TestExtractor, NAME
        _json = {'T2L-249': {'Status': 'PASS', 'Reporter': 'Tester'}}
        instance = TestExtractor(NAME, False)
        instance.generate_excel(_json)
        os.chdir(NAME)
        path, file = instance.search_import_file(NAME, "_1.xlsx")
        os.chdir(self.wdirectory)
        assert os.path.isfile(path) is True
        os.remove(path)

    def test_generate_excel_BarrosExtractor(self) -> None:
        from barros_request import BarrosExtractor, NAME
        _json = {'T2L-249': {'Status': 'To be tested', 'Summary': 'Disable values in CUSTOMER.CHARGE local ref Service Type', 'Bug_1_status': 'Closed', 'Bug_1_url': 'http'}}
        instance = BarrosExtractor(NAME, False)
        instance.generate_excel(_json)
        os.chdir(NAME)
        path, file = instance.search_import_file(NAME, "_1.xlsx")
        os.chdir(self.wdirectory)
        assert os.path.isfile(path) is True
        os.remove(path)    
        
    '''
    Mocking tests
    
    dict_keys(['T2L-255', 'T2L-252', 'T2L-251', 'T2L-250', 'T2L-249', 'T2L-248', 'T2L-247', 'T2L-243', 'T2L-242', 'T2L-241', 'T2L-239', 'T2L-238', 'T2L-231', 'T2L-228', 'T2L-219', 'T2L-218', 'T2L-212', 'T2L-211', 'T2L-210', 'T2L-208', 'T2L-206', 'T2L-204', 'T2L-202', 'T2L-187', 'T2L-186', 'T2L-161', 'T2L-141', 'T2L-139', 'T2L-137', 'T2L-136', 'T2L-132', 'T2L-124', 'T2L-117', 'T2L-78', 'T2L-76', 'T2L-71', 'T2L-44', 'T2L-42', 'T2L-21', 'T2L-19', 'T2L-13', 'T2L-12'])
    
    1. Simulate the impact an external service outages has on the rest of the test suite --> grab ticket raises timeout because requests throws an exception
    2. Test the except part of a try except block to see if they indeed prevent system crash
    3. understand how many times the requests.get method is called in an execution
    4. limit variability in the tests
    @patch('base_class.requests')
    or with patch('base_class.requests') as mock_requests:
    
    '''

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_grab_tickets_timeout(self) -> None:
        with patch('base_class.requests') as mock_requests:
            from deployment_log_UAT import DeployExtractor, NAME

            json_res = {'total':1, 'issues': [{"key":'T2L-422',"fields":{'summary': 'Test Summary', 'customfield_13191': None}}]}
            
            # Create a new Mock to imitate a Response
            response_mock = Mock()
            response_mock.json.return_value = json_res
            
            # Set the side effect of requests.get()
            mock_requests.get.side_effect = [Timeout, response_mock, response_mock]
            instance = DeployExtractor(NAME, False)
            if not found_cache():
                with self.assertRaises(Timeout):
                    inst = instance.grab_tickets(dict())
                    assert isinstance(inst, dict)
                    assert inst == json_res
                    mock_requests.get.assert_called_once()
                assert instance.grab_tickets(dict())['T2L-422']['summary'] == 'Test Summary'
                assert mock_requests.get.call_count == 3

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_call_count(self) -> None:
        with patch('base_class.requests') as mock_requests:
            from deployment_log_UAT import DeployExtractor, NAME
            DeployExtractor(NAME, False).grab_tickets(dict())
            assert mock_requests.get.call_count == 2

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_patch_ConnectionError(self) -> None:
        with patch('jira_routine_V2.requests') as mock_requests:
            from jira_routine_V2 import LogExtractor, NAME

            dic = dict()
            dic['T2L-249'] = grab_tickets_json['T2L-249']
            mock_requests.get.side_effect = [ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError]
            with self.assertRaises(ConnectionError):
                LogExtractor(NAME, False).clean_json(dic)
            configuration = Loader.grab_configuration(self)
            creds = f"Basic {configuration.u}"
            mock_requests.assert_has_calls([call.get(self.TEST_call_1, headers={'Authorization': creds, 'Content-Type': 'application/json'}, verify=False)])
            
    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_patch_JSONDecodeError(self) -> None:
        with patch('jira_routine_V2.requests') as mock_requests:
            from jira_routine_V2 import LogExtractor, NAME

            dic = dict()
            dic['T2L-249'] = grab_tickets_json['T2L-249']
            # Create a new Mock to imitate a Response
            response_mock = Mock()
            response_mock.json.return_value = {'total':1, 'issues': [{"key":'T2L-422',"fields":{'summary': 'Test Summary', 'customfield_13191': None}}]}
            
            mock_requests.get.side_effect = [response_mock, response_mock, response_mock, response_mock, response_mock, response_mock]
            mock_requests.get.json.side_effect = [JSONDecodeError, JSONDecodeError, JSONDecodeError, JSONDecodeError, JSONDecodeError, JSONDecodeError]
            
            with self.assertRaises(KeyError):
                LogExtractor(NAME, False).clean_json(dic)
                
    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linkedIssues_ConnectionError_real_data(self) -> None:
        with patch('base_class.requests') as mock_requests:
            from test_extraction_V2 import TestExtractor, NAME
            from deployment_log_UAT import DeployExtractor
            from barros_request import BarrosExtractor
            dic = dict()
            dic['T2L-249'] = grab_tickets_json['T2L-249']
            
            mock_requests.get.side_effect = [ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError]
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                TestExtractor(NAME, False).clean_json(dic)
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                DeployExtractor(NAME, False).clean_json(dic)
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                BarrosExtractor(NAME, False).clean_json(dic)
            configuration = Loader.grab_configuration(self)
            creds = f"Basic {configuration.u}"
            mock_requests.assert_has_calls([call.get(self.TEST_call_2, headers={'Authorization': creds, 'Content-Type': 'application/json'}, verify=False)])

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linkedIssues_JSONDecodeError_real_data(self) -> None:
        with patch('base_class.requests') as mock_requests:
            from test_extraction_V2 import TestExtractor, NAME
            from deployment_log_UAT import DeployExtractor
            from barros_request import BarrosExtractor
            dic = dict()
            dic['T2L-249'] = grab_tickets_json['T2L-249']
            # Create a new Mock to imitate a JSONDecodeError Response once the requests.get.json is triggered
            response_mock = Mock()
            response_mock.json.return_value = JSONDecodeError
            
            mock_requests.get.side_effect = [response_mock, response_mock, response_mock, response_mock, response_mock, response_mock]
            with self.assertRaises(TypeError): # testing 2 linked tickets so the asynchronous call is triggered
                print(TestExtractor(NAME, False).clean_json(dic))
            with self.assertRaises(TypeError): # testing 2 linked tickets so the asynchronous call is triggered
                DeployExtractor(NAME, False).clean_json(dic)
            with self.assertRaises(TypeError): # testing 2 linked tickets so the asynchronous call is triggered
                BarrosExtractor(NAME, False).clean_json(dic)
            
    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linkedIssues_TypeError_1link(self) -> None:
        with patch('base_class.BaseExtractor.consult_url') as mock_consult_url:
            from test_extraction_V2 import TestExtractor, NAME
            from deployment_log_UAT import DeployExtractor
            from barros_request import BarrosExtractor
            # testing 1 linked tickets so that the regular request.get call is triggered
            dic = dict()
            dic['T2L-249'] = {'issuelinks': [{'id': '418945', 'self': 'https://jira.com/rest/api/2/issueLink/418945', 'type': {'id': '10031', 'name': 'Cause', 'inward': 'is caused by', 'outward': 'causes', 'self': 'https://jira.com/rest/api/2/issueLinkType/10031'}, 'inwardIssue': {'id': '433704', 'key': 'EUHT-7091', 'self': 'https://jira.com/rest/api/2/issue/433704', 'fields': {'summary': 'T24 - Interface - Temos : Negative MD amounts for Guarantees', 'status': {'self': 'https://jira.com/rest/api/2/status/6', 'description': 'The issue is considered finished, the resolution is correct. Issues which are closed can be reopened.', 'iconUrl': 'https://jira.com/images/icons/statuses/closed.png', 'name': 'Closed', 'id': '6', 'statusCategory': {'self': 'https://jira.com/rest/api/2/statuscategory/3', 'id': 3, 'key': 'done', 'colorName': 'green', 'name': 'Done'}}, 'priority': {'self': 'https://jira.com/rest/api/2/priority/3', 'iconUrl': 'https://jira.com/images/icons/priorities/major.svg', 'name': 'Major', 'id': '3'}, 'issuetype': {'self': 'https://jira.com/rest/api/2/issuetype/1', 'id': '1', 'description': 'A problem which impairs or prevents the functions of the product.', 'iconUrl': 'https://jira.com/secure/viewavatar?size=xsmall&avatarId=15923&avatarType=issuetype', 'name': 'Bug', 'subtask': False, 'avatarId': 15923}}}}]}
            
            # Create a new Mock to imitate a Response
            response_mock = Mock()
            response_mock.json.return_value = JSONDecodeError
            mock_consult_url.side_effect = [response_mock, response_mock, response_mock, response_mock]
            
            with self.assertRaises(TypeError): # testing 1 linked tickets so that the regular request.json call is triggered 
                TestExtractor(NAME, False).clean_json(dic)
            with self.assertRaises(TypeError): # testing 1 linked tickets so that the regular request.json call is triggered 
                DeployExtractor(NAME, False).clean_json(dic)
            with self.assertRaises(TypeError): # testing 1 linked tickets so that the regular request.json call is triggered 
                BarrosExtractor(NAME, False).clean_json(dic)
    
    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linkedIssues_ConnectionError_2links(self) -> None:
        with patch('base_class.BaseExtractor.grab_linked_tickets') as mock_grab_linked_tickets:
            from test_extraction_V2 import TestExtractor, NAME
            from deployment_log_UAT import DeployExtractor
            from barros_request import BarrosExtractor
            # testing 2 linked tickets so that the asynchronous call is triggered
            dic = dict()
            dic['T2L-249'] = {'issuelinks': [{'id': '419070', 'self': 'https://jira.com/rest/api/2/issueLink/419070', 'type': {'id': '10031', 'name': 'Cause', 'inward': 'is caused by', 'outward': 'causes', 'self': 'https://jira.com/rest/api/2/issueLinkType/10031'}, 'outwardIssue': {'id': '430893', 'key': 'CM-31975', 'self': 'https://jira.com/rest/api/2/issue/430893', 'fields': {'summary': 'T24 TEMOS MCO changes', 'status': {'self': 'https://jira.com/rest/api/2/status/6', 'description': 'The issue is considered finished, the resolution is correct. Issues which are closed can be reopened.', 'iconUrl': 'https://jira.com/images/icons/statuses/closed.png', 'name': 'Closed', 'id': '6', 'statusCategory': {'self': 'https://jira.com/rest/api/2/statuscategory/3', 'id': 3, 'key': 'done', 'colorName': 'green', 'name': 'Done'}}, 'issuetype': {'self': 'https://jira.com/rest/api/2/issuetype/21', 'id': '21', 'description': 'Request for a Normal Change', 'iconUrl': 'https://jira.com/secure/viewavatar?size=xsmall&avatarId=18724&avatarType=issuetype', 'name': 'Normal Change', 'subtask': False, 'avatarId': 18724}}}}, {'id': '418945', 'self': 'https://jira.com/rest/api/2/issueLink/418945', 'type': {'id': '10031', 'name': 'Cause', 'inward': 'is caused by', 'outward': 'causes', 'self': 'https://jira.com/rest/api/2/issueLinkType/10031'}, 'inwardIssue': {'id': '433704', 'key': 'EUHT-7091', 'self': 'https://jira.com/rest/api/2/issue/433704', 'fields': {'summary': 'T24 - Interface - Temos : Negative MD amounts for Guarantees', 'status': {'self': 'https://jira.com/rest/api/2/status/6', 'description': 'The issue is considered finished, the resolution is correct. Issues which are closed can be reopened.', 'iconUrl': 'https://jira.com/images/icons/statuses/closed.png', 'name': 'Closed', 'id': '6', 'statusCategory': {'self': 'https://jira.com/rest/api/2/statuscategory/3', 'id': 3, 'key': 'done', 'colorName': 'green', 'name': 'Done'}}, 'priority': {'self': 'https://jira.com/rest/api/2/priority/3', 'iconUrl': 'https://jira.com/images/icons/priorities/major.svg', 'name': 'Major', 'id': '3'}, 'issuetype': {'self': 'https://jira.com/rest/api/2/issuetype/1', 'id': '1', 'description': 'A problem which impairs or prevents the functions of the product.', 'iconUrl': 'https://jira.com/secure/viewavatar?size=xsmall&avatarId=15923&avatarType=issuetype', 'name': 'Bug', 'subtask': False, 'avatarId': 15923}}}}]}
            # Create a new Mock to imitate a Response
            
            mock_grab_linked_tickets.side_effect = [ConnectionError, ConnectionError, ConnectionError, ConnectionError]
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                TestExtractor(NAME, False).clean_json(dic) 
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                DeployExtractor(NAME, False).clean_json(dic)
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                BarrosExtractor(NAME, False).clean_json(dic)

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_watchers_ConnectionError(self) -> None:
        with patch('jira_routine_V2.requests') as mock_requests:
            from jira_routine_V2 import LogExtractor, NAME
            dic = dict()
            dic['T2L-249'] = grab_tickets_json['T2L-249']
            mock_requests.get.side_effect = [ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError]
            with self.assertRaises(ConnectionError): # testing 2 linked tickets so the asynchronous call is triggered
                LogExtractor(NAME, False).clean_json(dic)
                
    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linked_ticket_TestExtractor(self) -> None:
        with patch('base_class.BaseExtractor.consult_url') as mock_consult_url:
            
            # Create a new Mock to imitate a Response
            response_mock = Mock()
            response_mock.json.return_value = {'fields': {'issuetype': {'name': 'Bug'}, 'summary': 'Yellow Bug'}}
            mock_consult_url.side_effect = [response_mock, response_mock, response_mock, response_mock]
            
            from test_extraction_V2 import TestExtractor, NAME
            _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'issuelinks': [{'outwardIssue': {'key': 'T2L-250'}}]}}
            instance = TestExtractor(NAME, False)
            instance.base_url = 'http://'
            _json = instance.clean_json(_json)
            assert _json['T2L-249']['Bug_1_summary'] == 'Yellow Bug'
            assert _json['T2L-249']['Bug_1_url'] == 'http://T2L-250'

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linked_tickets_TestExtractor(self) -> None:
        with patch('base_class.BaseExtractor.grab_linked_tickets') as mock_grab_linked_tickets:
            
            # Create a new Mock to imitate a Response
            response_mock = {'T2L-250': {'issuetype': {'name': 'Bug'}, 'summary': 'Yellow Bug'}, 'T2L-251': {'issuetype': {'name': 'Bug'}, 'summary': 'Blue Bug'}}
            mock_grab_linked_tickets.side_effect = [response_mock, response_mock, response_mock, response_mock]
            
            from test_extraction_V2 import TestExtractor, NAME
            _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'issuelinks': [{'inwardIssue': {'key': 'T2L-250'}}, {'outwardIssue': {'key': 'T2L-251'}}]}}
            instance = TestExtractor(NAME, False)
            instance.base_url = 'http://'
            _json = instance.clean_json(_json)
            assert _json['T2L-249']['Bug_1_summary'] == 'Yellow Bug'
            assert _json['T2L-249']['Bug_2_summary'] == 'Blue Bug'
            assert _json['T2L-249']['Bug_1_url'] == 'http://T2L-250'
            assert _json['T2L-249']['Bug_2_url'] == 'http://T2L-251'

    @unittest.skipIf(found_cache() is True, "No HTTP request as grab_tickets is cached")
    def test_clean_json_linked_ticket_BarrosExtractor(self) -> None:
        with patch('base_class.BaseExtractor.consult_url') as mock_consult_url:
            
            # Create a new Mock to imitate a Response
            response_mock = Mock()
            response_mock.json.return_value = {'fields': {'issuetype': {'name': 'Bug'}, 'summary': 'Red Bug'}}
            mock_consult_url.side_effect = [response_mock, response_mock, response_mock, response_mock]
            
            from test_extraction_V2 import TestExtractor, NAME
            _json = {'T2L-249': {'Reporter': 'Tester', 'issuetype': {'name': 'Test'}, 'issuelinks': [{'outwardIssue': {'key': 'EUHT-1'}}]}}
            instance = TestExtractor(NAME, False)
            instance.base_url = 'http://'
            _json = instance.clean_json(_json)
            assert _json['T2L-249']['Bug_1_summary'] == 'Red Bug'
            assert _json['T2L-249']['Bug_1_url'] == 'http://EUHT-1'

    @patch('jira_routine_V2.logging')
    @patch('jira_routine_V2.requests')
    def test_clean_json_watchers_ConnectionError_logger(self, mock_requests, mock_log) -> None:
        from jira_routine_V2 import LogExtractor, NAME
        dic = dict()
        dic['T2L-249'] = grab_tickets_json['T2L-249']

        mock_requests.get.side_effect = [ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError, ConnectionError]
        with self.assertRaises(ConnectionError):
            try:
                logger = mock_log.error("BB")
                logger.level = logging.ERROR
                stream_handler = logging.StreamHandler(sys.stdout)
                logger.addHandler(stream_handler)
                _, mock_log = LogExtractor(NAME, False).clean_json(dic, mock_log)
            finally:
                logger.removeHandler(stream_handler)
                mock_log.error.assert_called_with("BB")
                print(mock_log.mock_calls)

if __name__ == '__main__':
#    unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(BeforeProgramStartTests("test_clean_json_watchers_ConnectionError_logger"))
    runner = unittest.TextTestRunner()
    runner.run(suite)


