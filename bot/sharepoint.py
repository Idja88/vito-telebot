import requests
import json
import os
import re
from requests_ntlm import HttpNtlmAuth

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(ROOT_DIR, 'config.json')

with open(config_path) as config_file:
    config = json.load(config_file)
    spconfig = config['sharepoint']

USERNAME = spconfig['user']
PASSWORD = spconfig['password']
SHAREPOINT_URL = spconfig['url']
SUBSCRIBER_LIST = spconfig['subscriber_list']
PHONE_FIELD = spconfig['phone_field']
CHAT_FIELD = spconfig['chat_field']
AUTH = HttpNtlmAuth(USERNAME, PASSWORD)
HEADERS = {'Accept': 'application/json;odata=verbose',"content-type": "application/json;odata=verbose"}

def get_token():
        contextinfo_api = f"{SHAREPOINT_URL}/_api/contextinfo"
        try:
                with requests.post(contextinfo_api, auth=AUTH, headers=HEADERS) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json['d']['GetContextWebInformation']['FormDigestValue']
                        return value
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def get_subscriber_id(chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')/items?$filter={CHAT_FIELD} eq '{chat}'"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json["d"]["results"]
                        return value[0]["Id"]
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None
        
def get_list_entity():
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')?$select=ListItemEntityTypeFullName"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json["d"]["ListItemEntityTypeFullName"]
                        return value
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def add_subscriber(phone, chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')/items"
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
                      response_json = json.loads(response.text)
                      return response_json
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None
        
def check_subscriber(chat):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')/items?$filter={CHAT_FIELD} eq '{chat}'"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json["d"]["results"]
                        return value
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def delete_subscriber(chat):
        id = get_subscriber_id(chat)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')/Items({id})"
        delete_headers = HEADERS.copy()
        delete_headers['X-Http-Method'] = 'DELETE'
        delete_headers['If-Match'] = '*'
        delete_headers['X-RequestDigest'] = get_token()
        try: 
                with requests.post(list_url, auth=AUTH, headers=delete_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        return response_json
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def update_subscriber(id, phone):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')/Items({id})"
        entity = get_list_entity()
        data = {
              '__metadata':  {'type': entity},
              'Title': phone
              }
        upd_headers = HEADERS.copy()
        upd_headers['X-Http-Method'] = 'MERGE'
        upd_headers['If-Match'] = '*'
        try:
                with requests.post(list_url, verify=False, auth=AUTH, headers=upd_headers, data=json.dumps(data)) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        return response_json
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def get_last_token():
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/GetChanges"
        data = {'query': 
                {'__metadata': {'type': 'SP.ChangeQuery'}, 
                'Add': True, 
                'Item': True
                }
        }
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.post(list_url, verify=False, auth=AUTH, headers=get_headers, data=json.dumps(data)) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json['d']['results']
                        return value[-1]["ChangeToken"]['StringValue']
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

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
                try:
                        with requests.post(list_url, verify=False, auth=AUTH, headers=get_headers, data=json.dumps(data)) as response:
                                response.raise_for_status()
                                response_json = json.loads(response.text)
                                results = response_json['d']['results']
                                if results:
                                        created_item = results[0]
                                        task_id = created_item['ItemId']
                                        return task_id
                except requests.exceptions.RequestException as e:
                        print(f"Error occurred: {e}")
                        return None
        else:
                return None

def get_task_assignedto_orgid(task_id, chat_data):
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Задачи рабочих процессов (Vitro)')/items({task_id})"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        chat_data['TaskId'] = response_json["d"]["Id"]
                        value = response_json["d"]['VitroWorkflowAssignedTo']
                        return value
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def get_task_assignedto_fizid(task_id, chat_data):
        org_id = get_task_assignedto_orgid(task_id, chat_data)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Организационно-штатная структура')/items({org_id})?$select=VitroOrgPerson"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json["d"]['VitroOrgPerson']
                        return value
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def get_task_assignedto_phone(task_id, chat_data):
        fiz_id = get_task_assignedto_fizid(task_id, chat_data)
        list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('Физические лица')/items({fiz_id})?$select=VitroOrgPhone"
        get_headers = HEADERS.copy()
        get_headers['X-RequestDigest'] = get_token()
        try:
                with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                        response.raise_for_status()
                        response_json = json.loads(response.text)
                        value = response_json["d"]['VitroOrgPhone']
                        return value if value else None
        except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
                return None

def is_assignedto_subscriber(task_id, chat_data):
        if task_id is None:
                return False
        phone = get_task_assignedto_phone(task_id, chat_data)
        if phone is None: 
                return False
        else:
                phone = re.sub('[^A-Za-z0-9]+', '', phone)
                list_url = f"{SHAREPOINT_URL}/_api/Web/Lists/GetByTitle('{SUBSCRIBER_LIST}')/items?$filter={PHONE_FIELD} eq '{phone}'"
                get_headers = HEADERS.copy()
                get_headers['X-RequestDigest'] = get_token()
                try:
                        with requests.get(list_url, verify=False, auth=AUTH, headers=get_headers) as response:
                                response.raise_for_status()
                                response_json = json.loads(response.text)
                                value = response_json["d"]["results"]
                                chat_data['TeleChat'] = value[0]["TeleChat"]
                                return bool(value)
                except requests.exceptions.RequestException as e:
                        print(f"Error occurred: {e}")
                        return False