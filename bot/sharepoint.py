import requests
import json
import os
from requests_ntlm import HttpNtlmAuth

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = '\\'.join([ROOT_DIR, 'config.json'])

with open(config_path) as config_file:
    config = json.load(config_file)
    spconfig = config['share_point']

USERNAME = spconfig['user']
PASSWORD = spconfig['password']
SHAREPOINT_URL = spconfig['url']
SHAREPOINT_DESIGN = spconfig['design']
SHAREPOINT_PUBLIC = spconfig['public']
SHAREPOINT_DOC = spconfig['doc_library']
SHAREPOINT_LIST = spconfig['list']
AUTH = HttpNtlmAuth(USERNAME,PASSWORD)
HEADERS = {'Accept': 'application/json;odata=verbose',"content-type": "application/json;odata=verbose"}

def getToken():
        contextinfo_api = f"{SHAREPOINT_URL}/_api/contextinfo"
        response = requests.post(contextinfo_api,auth=AUTH,headers=HEADERS)
        response = json.loads(response.text)
        digest_value = response['d']['GetContextWebInformation']['FormDigestValue']
        return digest_value

def get_listitemid(chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items?$filter=startswith(Chat,'{chat}')"
        response = requests.get(list_url,verify=False,auth=AUTH,headers=HEADERS)
        response = json.loads(response.text)
        value = response["d"]["results"]
        return value[0]["Id"]

def new_subscriber(title,chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items"
        data = {
              '__metadata':  {'type': 'SP.Data.TestListItem' },
              'Title': title,
              'Chat': chat
              }
        new_headers = HEADERS
        new_headers['X-RequestDigest']=getToken()
        response = requests.post(list_url,auth=AUTH,headers=new_headers,data=json.dumps(data))
        return json.loads(response.text)

def check_phone(chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items?$filter=startswith(Chat,'{chat}')"
        response = requests.get(list_url,verify=False,auth=AUTH,headers=HEADERS)
        response = json.loads(response.text)
        value = response["d"]["results"]
        return value

def delete_subscriber(chat):
        id = get_listitemid(chat)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/Items({id})"
        new_headers = HEADERS
        new_headers['X-Http-Method']='DELETE' #to delete
        new_headers['If-Match']='*' #to delete
        new_headers['X-RequestDigest']=getToken()
        response = requests.post(list_url, auth=AUTH,headers=new_headers)
        return response

def update_item(id,phone):
        update_api = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/Items({id})"
        data = {
              '__metadata':  {'type': 'SP.Data.TestListItem' },
              'Title': phone
              }
        new_headers = HEADERS
        new_headers['X-Http-Method']='MERGE' #to update
        new_headers['If-Match']='*' #to update
        response = requests.post(update_api, auth=AUTH,headers=new_headers,data=json.dumps(data))
        return json.loads(response.text)

def get_last_token():
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/GetChanges"
        data = { 'query': 
                { '__metadata': { 'type': 'SP.ChangeQuery' }, 
                'Add': True, 
                'Item': True
                }
        }
        new_headers = HEADERS
        new_headers['X-RequestDigest']=getToken()
        response = requests.post(list_url,verify=False,auth=AUTH,headers=HEADERS,data=json.dumps(data))
        response = json.loads(response.text)
        value = response['d']['results']
        return value[-1]["ChangeToken"]['StringValue']

def get_changes():
        token = get_last_token()
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/GetChanges"
        data = { 'query': 
                { '__metadata': { 'type': 'SP.ChangeQuery' }, 
                'Add': True, 
                'Item': True,
                "ChangeTokenStart": {"__metadata":{"type":"SP.ChangeToken"},"StringValue": token}
                }
        }
        new_headers = HEADERS
        new_headers['X-RequestDigest']=getToken()
        response = requests.post(list_url,verify=False,auth=AUTH,headers=HEADERS,data=json.dumps(data),timeout=120)
        response = json.loads(response.text)
        value = response['d']['results']
        return value

def get_token_changes():
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/getlistitemchangessincetoken"
        data = {'query': {'__metadata': {'type': 'SP.ChangeLogItemQuery'}, 'ChangeToken': '1;3;cdaf6bfd-6813-4fd3-bc9c-eaa6998e7544;637592758710830000;319924'}}
        new_headers = HEADERS
        new_headers['X-RequestDigest']=getToken()
        response = requests.post(list_url,verify=False,auth=AUTH,headers=HEADERS,data=json.dumps(data),timeout=120)
        #response = json.loads(response.text)
        #value = response['d']['results']
        return response.text

#print(get_last_token())
#print(get_changes())
#print(get_token_changes())

while True:
       print(get_changes())