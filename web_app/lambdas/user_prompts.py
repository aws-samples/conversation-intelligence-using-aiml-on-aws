import json
import os
import boto3
import time
import uuid
from decimal import Decimal

tableName = os.environ["CustomPromptsTable"]
table = boto3.resource("dynamodb").Table(tableName)

# defined constants
GROUP_TYPE_INFO = 'GROUP_INFO'
GROUP_TYPE_DETAIL = 'GROUP_DETAIL'
STATUS_SUCCESS = 'SUCCESS'
STATUS_INVALID_ACTION = 'INVALID ACTION'
STATUS_NOT_FOUND = 'NOT FOUND'

# Handle All Actions for Groups
def group_actions(event):
    response = { 'data' : None , 'status' : "" }
    action = event["pathParameters"]["key"]
    payload = json.loads(event["body"])
    
    payload_userid = payload["userid"]
    payload_id = payload.get('id', uuid.uuid4().hex)
    payload_title = payload.get('title', '')
    payload_description = payload.get('description', '')

    db_key = { 'user_id': payload_userid, 'type':GROUP_TYPE_INFO}

    db_output = table.get_item(Key = db_key)

    if action == "add":
        # Creating New Group
        group = { 'group_id': payload_id, 'title': payload_title, 'description': payload_description, 'current_version': 0 , 'is_deleted': False}
        
        # Check if data exists
        if "Item" in db_output :
            new_group_obj = db_output["Item"]["grouplist"]
            new_group_obj.append(json.loads(json.dumps(group), parse_float=Decimal))
            db_obj = {
                'user_id': payload_userid,
                'type':GROUP_TYPE_INFO,
                'grouplist': new_group_obj
            }
        else :
            db_obj = {
                'user_id': payload_userid,
                'type':GROUP_TYPE_INFO,
                'grouplist': [json.loads(json.dumps(group), parse_float=Decimal)]
            }

        response['data'] = table.put_item(Item = db_obj)
        response['status'] = STATUS_SUCCESS

    elif action == "update":
        # Check if data exists
        if "Item" in db_output :
            group_list = db_output["Item"]["grouplist"]
            new_group_obj = []
            for index in range(len(group_list)):
                if group_list[index]["group_id"] == payload_id:
                    group = { 'group_id': payload_id, 'title': payload_title, 'description': payload_description, 'current_version': group_list[index]['current_version'], 'is_deleted': False}
                    new_group_obj.append(json.loads(json.dumps(group, default=str)))
                else:
                    new_group_obj.append(group_list[index])
            
            db_obj = {
                'user_id': payload_userid,
                'type':GROUP_TYPE_INFO,
                'grouplist': new_group_obj
            }
            response['data'] = table.put_item(Item = db_obj)
            response['status'] = STATUS_SUCCESS
        else:
            response['status'] = STATUS_NOT_FOUND
    elif action == "delete":
        # Check if data exists
        if "Item" in db_output :
            group_list = db_output["Item"]["grouplist"]
            new_group_obj = []
            for index in range(len(group_list)):
                if group_list[index]["group_id"] == payload_id:
                    group = { 'group_id': payload_id, 'title': group_list[index]['title'], 'description': group_list[index]['description'], 'current_version': group_list[index]['current_version'], 'is_deleted': True}
                    new_group_obj.append(group)
                else:
                    new_group_obj.append(group_list[index])
            
            new_group_obj = json.loads(json.dumps(new_group_obj, default=str))
            db_obj = {
                'user_id': payload_userid,
                'type':GROUP_TYPE_INFO,
                'grouplist': new_group_obj
            }
            response['data'] = table.put_item(Item = db_obj)
            response['status'] = STATUS_SUCCESS
        else:
            response['status'] = STATUS_NOT_FOUND
    elif action == "get":
        if "Item" in db_output:
            group_list = db_output["Item"]["grouplist"]
            # Get list of non deleted groups
            group_filter_list = [item for item in group_list if item.get('is_deleted')==False]
            output = {'user_id': db_output["Item"]["user_id"], 'type': GROUP_TYPE_INFO , 'grouplist': group_filter_list}
            response['data'] = json.loads(json.dumps(output, default=str))
            response['status'] = STATUS_SUCCESS
        else:
            response['status'] = STATUS_NOT_FOUND
    else:
        response['status'] = STATUS_INVALID_ACTION

    return response

# Handle All Actions for Group Details
def group_detail_actions(event):
    response = { 'data' : None , 'status' : "" }
    action = event["pathParameters"]["key"]
    payload = json.loads(event["body"])
    
    payload_user_id = payload["userid"]
    payload_group_id = payload["groupid"]
    
    # Get Group Information
    db_group_key = { 'user_id': payload_user_id, 'type':GROUP_TYPE_INFO}
    db_group_output = table.get_item(Key = db_group_key)
    
    if "Item" in db_group_output:
        group_list = db_group_output["Item"]["grouplist"]
        group_infolist_detail = [item for item in group_list if item.get('group_id')==payload_group_id]
        group_current_version = group_infolist_detail[0]["current_version"]
        group_next_version = int(group_current_version) + 1
        
        if action == "add":
            payload_promptlist = payload["promptlist"]
            new_group_detail = { 
                'user_id': payload_user_id, 
                'type':f'{GROUP_TYPE_DETAIL}_{payload_group_id}_v{group_next_version}',
                'promptList': payload_promptlist,
                'created_on': int(time.time())
            }
            group_detail_object = json.loads(json.dumps(new_group_detail), parse_float=Decimal)
            response['data'] = table.put_item(Item = group_detail_object)
                
            # Update Group Version
            new_group_list = [];
            for index in range(len(group_list)):
                if group_list[index]["group_id"] == payload_group_id:
                    group_list[index]["current_version"] = group_next_version
                
                new_group_list.append(group_list[index])
            
            db_obj = {
                'user_id': payload_user_id,
                'type': GROUP_TYPE_INFO,
                'grouplist': new_group_list
            }
            table.put_item(Item = db_obj)
            response['status'] = STATUS_SUCCESS
        elif action == "get":
            if "Item" in db_group_output:
                # Get Group Information
                db_group_detail_key = { 'user_id': payload_user_id, 'type':f'GROUP_DETAIL_{payload_group_id}_v{group_current_version}'}
                db_group_detail_output = table.get_item(Key = db_group_detail_key)
                
                result = {
                    'user_id': payload_user_id,
                    'group_id': payload_group_id,
                    'group_info': group_infolist_detail,
                    'group_info_detail': []
                }
                
                if "Item" in db_group_detail_output:
                    result["group_info_detail"] = db_group_detail_output["Item"]
                    
                response['data'] = json.loads(json.dumps(result, default=str))
                response['status'] = STATUS_SUCCESS
        else:
            response['status'] = STATUS_INVALID_ACTION
    else:
        response['status'] = STATUS_NOT_FOUND
    return response


def handler(event, context):
    methodtype = event["httpMethod"]
    response = { 'data' : None , 'status' : "" }
    result = None
    
    if methodtype == "POST":
        section = json.loads(event["body"])["section"]
        if section == "GROUP":
            result = group_actions(event)
        elif section == "GROUPDETAIL" :
            result = group_detail_actions(event)
        else :
            result = response;
            result["status"] = "INVALID PAYLOAD"
    else:
        result = response;
        result["status"] = "INVALID REQUEST"
        
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Content-Type':'application/json'
        },
        "body": json.dumps(result)
    }