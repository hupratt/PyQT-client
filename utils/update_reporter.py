import requests, time
import json
import configuration as cfg 


liste = {'https://jira.com/rest/api/2/issue/T2L-249': 'John',
'https://jira.com/rest/api/2/issue/T2L-250': 'Jack',
}


#test on ONE issue first to see if the batch works
#headers = {"Authorization": "Basic %s" % cfg.u, "Content-Type": "application/json"}
#response = requests.put('https://jira.com/rest/api/2/issue/T2L-250', data=json.dumps({"update":{"reporter":[{"set":{'name':'Jack'}}]}}), headers=headers, verify = False)
#print(response.text)
#print(response)

headers = {"Authorization": "Basic %s" % cfg.u, "Content-Type": "application/json"}


for key, value in liste.items():
    response = requests.put(key, data=json.dumps({"update":{"reporter":[{"set":{'name':value}}]}}), headers=headers, verify = False)
    print(key,response.text)
    time.sleep(1)

print(response.text)
