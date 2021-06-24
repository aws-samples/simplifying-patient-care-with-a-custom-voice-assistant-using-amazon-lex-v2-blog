# SPDX-FileCopyrightText: Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os

dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    intent_name = event['sessionState']['intent']['name']
    current_slots = event['sessionState']['intent']['slots']
    patient_id = current_slots['PatientId']
    sensor_type = current_slots['SensorType']
    session_state = event['sessionState']
    source = event['invocationSource']
  
    query_result = ''
    if patient_id is None:
        msg = "What is the ID of the patient you wish to get information on?"
        return elicit_slot(session_state, 'PatientId', message(msg))
    else:
        patient = get_patient(patient_id)
        if patient['Count'] == 0:
            return elicit_slot(session_state, 'PatientId', message("Patient was not found. Please enter another patient's ID."))
        query_result = patient['Items']
    
    name = query_result[0]['NAME']['S']
    if sensor_type is None:
        msg = "What would you like to know about {}?".format(name)
        return elicit_slot(session_state, 'SensorType', message(msg))
    
    value = get_sensor_value(sensor_type['value']['interpretedValue'], query_result)
    if value is not None:
        msg = "The {} of {} is {}. Thank you".format(sensor_type['value']['interpretedValue'], name, get_unit(value, sensor_type['value']['interpretedValue']))
        return close(session_state, 'Fulfilled', message(msg))
    else:
        msg = "No {} is found for {}. Please try another sensor type.".format(sensor_type, name)
        return elicit_slot(session_attributes, 'SensorType', message(msg))
        
def get_unit(value, sensor_type):
    if sensor_type == 'blood pressure':
        blood_pressure = value.split('/')
        return  blood_pressure[0] + ' over ' + blood_pressure[1]
    elif sensor_type == 'blood glucose':
        return value + ' milligrams per decilitre'
    elif sensor_type == 'heart rate':
        return value + ' beats per minute'
    elif sensor_type == 'respiratory rate':
        return value + ' breaths per minute'
    elif sensor_type == 'body temperature':
        return value + ' degrees Farenheit'
    else:
        return value
        
def get_patient(patient_id):
    response = dynamodb.query(
            TableName = os.environ['PATIENT_TABLE'],
            KeyConditionExpression= 'PATIENT_ID = :PATIENT_ID',
            ExpressionAttributeValues = {
                ':PATIENT_ID':
                    {
                        'S': patient_id['value']['interpretedValue']
                    }
            }
    )
    return response
    
def get_sensor_value(sensor_type, query_result):
    timestamps = []
    for item in query_result:
        timestamps.append(item['TIMESTAMP']['S'])
    if not timestamps:
        return None
    latest = max(timestamps)
    value = ''
    for item in query_result:
        if item['TIMESTAMP']['S'] == latest:
            value = json.loads(item['DATA']['S'])[sensor_type.replace(" ", "_")]
    return value

def elicit_slot(session_state, slot_to_elicit, message):
    dialog_action = {
        'slotToElicit': slot_to_elicit,
        'type': 'ElicitSlot'
    }
    session_state['dialogAction'] = dialog_action
    return {
        'sessionState': session_state,
        'messages': message
    }


def close(session_state, fulfillment_state, message):
    dialog_action = {
        'type': 'Close'
    }
    session_state['dialogAction'] = dialog_action
    return {
        'sessionState': session_state,
        'messages': message
    }


def message(content):
    message = [{
        'contentType': 'PlainText',
        'content': content
    }]
    return message