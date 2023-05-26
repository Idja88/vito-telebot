import requests
import json
import os
import re
from requests_ntlm import HttpNtlmAuth

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = '\\'.join([ROOT_DIR, 'config.json'])

with open(config_path) as config_file:
    config = json.load(config_file)
    spconfig = config['share_point']

USERNAME = spconfig['user']
PASSWORD = spconfig['password']
SHAREPOINT_URL = spconfig['url']
SHAREPOINT_LIST = spconfig['list']
AUTH = HttpNtlmAuth(USERNAME,PASSWORD)
HEADERS = {'Accept': 'application/json;odata=verbose',"content-type": "application/json;odata=verbose"}

def get_token():
        contextinfo_api = f"{SHAREPOINT_URL}/_api/contextinfo"
        response = requests.post(contextinfo_api, auth=AUTH, headers=HEADERS)
        response = json.loads(response.text)
        digest_value = response['d']['GetContextWebInformation']['FormDigestValue']
        return digest_value

def get_subscriber_id(chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items?$filter=TeleChat eq '{chat}'"
        response = requests.get(list_url, verify=False, auth=AUTH, headers=HEADERS)
        response = json.loads(response.text)
        value = response["d"]["results"]
        return value[0]["Id"]

def get_list_entity():
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')?$select=ListItemEntityTypeFullName"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        response = requests.get(list_url, verify=False, auth=AUTH, headers=get_headers)
        response = json.loads(response.text)
        value = response["d"]["ListItemEntityTypeFullName"]
        return value

def add_subscriber(phone, chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items"
        entity = get_list_entity()
        data = {
              '__metadata':  {'type': entity },
              'TelePhone': phone,
              'TeleChat': chat
              }
        add_headers = HEADERS.copy()
        add_headers['X-RequestDigest'] = get_token()
        try:
               with requests.post(list_url, verify=False, auth=AUTH, headers=add_headers, data=json.dumps(data)) as response:
                      response.raise_for_status()
                      return json.loads(response.text)
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None
        
def check_subscriber(chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items?$filter=TeleChat eq '{chat}'"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        response = requests.get(list_url, verify=False, auth=AUTH, headers=get_headers)
        response = json.loads(response.text)
        value = response["d"]["results"]
        return value

def delete_subscriber(chat):
        id = get_subscriber_id(chat)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/Items({id})"
        delete_headers = HEADERS.copy()
        delete_headers['X-Http-Method'] = 'DELETE'
        delete_headers['If-Match'] = '*'
        delete_headers['X-RequestDigest'] = get_token()
        response = requests.post(list_url, auth=AUTH, headers=delete_headers)
        return response

def update_subscriber(id, phone):
        update_api = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/Items({id})"
        entity = get_list_entity()
        data = {
              '__metadata':  {'type': entity },
              'Title': phone
              }
        upd_headers = HEADERS.copy()
        upd_headers['X-Http-Method'] = 'MERGE'
        upd_headers['If-Match'] = '*'
        response = requests.post(update_api, auth=AUTH, headers=upd_headers, data=json.dumps(data))
        return json.loads(response.text)

def get_last_token():
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/GetChanges"
        data = {'query': 
                {'__metadata': { 'type': 'SP.ChangeQuery' }, 
                'Add': True, 
                'Item': True
                }
        }
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        response = requests.post(list_url, verify=False, auth=AUTH, headers=get_headers, data=json.dumps(data))
        response_json = json.loads(response.text)
        value = response_json['d']['results']
        return value[-1]["ChangeToken"]['StringValue']

def get_changes():
        token = get_last_token()
        if token:
                list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/GetChanges"
                data = {
                        'query': {
                        '__metadata': {'type': 'SP.ChangeQuery'},
                        'Add': True,
                        'Item': True,
                        "ChangeTokenStart": {
                                "__metadata": {"type": "SP.ChangeToken"},
                                "StringValue": token
                        }
                        }
                }
                get_headers = HEADERS.copy()
                get_headers['X-RequestDigest'] = get_token()
                response = requests.post(list_url, verify=False, auth=AUTH, headers=get_headers, data=json.dumps(data))
                response_json = json.loads(response.text)
                results = response_json['d']['results']
                if results:
                        created_item = results[0]
                        task_id = created_item['ItemId']
                        return task_id
        else:
                return None

def get_task_assignedto_OrgID(task_id, chat_data):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/items({task_id})"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        response = requests.get(list_url, verify=False, auth=AUTH, headers=get_headers)
        response = json.loads(response.text)
        chat_data['TaskId'] = response["d"]["Id"]
        value = response["d"]['VitroWorkflowAssignedTo']
        return value

def get_task_assignedto_FizID(task_id, chat_data):
        org_id = get_task_assignedto_OrgID(task_id, chat_data)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Организационно-штатная структура')/items({org_id})?$select=VitroOrgPerson"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        response = requests.get(list_url, verify=False, auth=AUTH, headers=get_headers)
        response = json.loads(response.text)
        value = response["d"]['VitroOrgPerson']
        return value

def get_task_assignedto_Phone(task_id, chat_data):
        fiz_id = get_task_assignedto_FizID(task_id, chat_data)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Физические лица')/items({fiz_id})?$select=VitroOrgPhone"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        response = requests.get(list_url, verify=False, auth=AUTH, headers=get_headers)
        response = json.loads(response.text)
        value = response["d"]['VitroOrgPhone']
        return value if value else None

def is_assignedto_subscriber(task_id, chat_data):
        if task_id is None:
                return False
        phone = get_task_assignedto_Phone(task_id, chat_data)
        if phone is None:
                return False
        else:
                phone = re.sub('[^A-Za-z0-9]+', '', phone)
                list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SHAREPOINT_LIST}')/items?$filter=TelePhone eq '{phone}'"
                get_headers = HEADERS.copy()
                get_headers['X-RequestDigest'] = get_token()
                response = requests.get(list_url, verify=False, auth=AUTH, headers=get_headers)
                response = json.loads(response.text)
                value = response["d"]["results"]
                chat_data['TeleChat'] = value[0]["TeleChat"]
                return bool(value)