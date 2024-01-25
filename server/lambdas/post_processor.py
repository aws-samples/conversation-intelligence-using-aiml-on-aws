#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import decimal
import json
import math
import os
import tarfile
from datetime import datetime
from decimal import Context
import re
import server_constants
import pickle

import boto3

print("Loading Post Processor...")
s3_client = boto3.client("s3")
tableName = os.environ["UploadsTable"]
table = boto3.resource("dynamodb").Table(tableName)
dynamo_client = boto3.client("dynamodb")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return math.floor(float(o))
        return super().default(o)


def calc_seconds(full_time_str):
    micro_second_split = full_time_str.split(".")
    time_str = str(micro_second_split[0])
    time_split = time_str.split(":")
    total_sec = int(time_split[0]) * 3600 + int(time_split[1]) * 60 + int(time_split[2])
    return str(total_sec) + "." + micro_second_split[1]


def handler(e, context):
    event = e["event"]
    s3_bucket = event["bucket"]
    key = event["key"]
    content_type = event['content_type']
    output_key = event["output_s3_key"]
    input_file = event["input_file"]
    groups_file = event["groups"]
    diarization_file = event["diarization_file"]
    original_transcription_file = event["original_transcription_file"]
    sentiment_job_output_file = event["sentiment_job_output_file"]
    entities_job_output_file = event["entities_job_output_file"]
    language = event["dominant_language_code"]
    dominant_language = event["dominant_language"]
    summarization_result = event["Summarization"]
    action_items = event["ActionItems"]
    topic = event["Topic"]
    politeness = event["Politeness"]
    callback_value = event["Callback"]
    product = event["Product"]
    resolution = event["Resolution"]
    agent_sentiment = event["AgentSentiment"]
    customer_sentiment = event["CustomerSentiment"]
    total_duration = 0.0
    customer_duration = 0.0
    agent_duration = 0.0

    # Download original transcript file
    temp_transcription_file_path = "/tmp/" + original_transcription_file
    s3_client.download_file(
        s3_bucket,
        f"{output_key}/{original_transcription_file}",
        temp_transcription_file_path,
    )
    temp_transcription_file = open(temp_transcription_file_path, "r")
    temp_transcription_file_lines = temp_transcription_file.readlines()
    temp_transcription_file.close()
    translated_conversation_dict = dict()
    temp_translation_file_lines = None

    # Download original transcript file
    translated_file_name = original_transcription_file
    if language != "original" and language != "en":
        translated_file_name = original_transcription_file.replace(
            "original", "translated"
        ).replace("en", "translated")

        temp_translated_file_path = "/tmp/" + translated_file_name
        s3_client.download_file(
            s3_bucket,
            f"{output_key}/{translated_file_name}",
            temp_translated_file_path,
        )
        temp_translation_file = open(temp_translated_file_path, "r")
        temp_translation_file_lines = temp_translation_file.readlines()
        temp_translation_file.close()

        for i, text in enumerate(temp_translation_file_lines):
            translated_conversation_dict[i] = text

    # Download and process Sentiment data
    head, file_name = os.path.split(sentiment_job_output_file)
    temp_sentiment_file_path = "/tmp/sentiment-" + file_name
    s3_client.download_file(
        s3_bucket, f"{sentiment_job_output_file}", temp_sentiment_file_path
    )

    # Process Sentiment Output File
    tar = tarfile.open(temp_sentiment_file_path, "r:gz")
    sentiment_object = dict()
    for member in tar.getmembers():
        f = tar.extractfile(member)
        if f is not None:
            line_by_line_sentiment = f.readlines()
            if line_by_line_sentiment:
                for i, text in enumerate(line_by_line_sentiment):
                    json_object = json.loads(text)
                    sentiment_object[json_object["Line"]] = json_object
    tar.close()

    # Download and process Sentiment data
    entities_head, entities_file_name = os.path.split(entities_job_output_file)
    temp_entities_file_path = "/tmp/entities-" + entities_file_name
    s3_client.download_file(
        s3_bucket, f"{entities_job_output_file}", temp_entities_file_path
    )

    # Process Sentiment Output File
    entities_tar = tarfile.open(temp_entities_file_path, "r:gz")
    entities_object = dict()
    for member in entities_tar.getmembers():
        f = entities_tar.extractfile(member)
        if f is not None:
            line_by_line_entities = f.readlines()
            if line_by_line_entities:
                for i, text in enumerate(line_by_line_entities):
                    json_object = json.loads(text)
                    entities_object[json_object["Line"]] = json_object
    entities_tar.close()

    # Download Group
    tmp_groups_path = "/tmp/" + groups_file
    s3_client.download_file(s3_bucket, f"{output_key}/{groups_file}", tmp_groups_path)
    group_file = open(tmp_groups_path, "rb")
    groups = pickle.load(group_file)
    group_file.close()

    transcript_speech_segments = []
    sentiment_list = []
    entities_list = []
    for i, text in enumerate(temp_transcription_file_lines):
        conversation_str = str(text).strip()
        conversation_split = conversation_str.split(":", 1)
        speaker = conversation_split[0].strip()
        chat = conversation_split[1].strip()

        transcript_segment_object = {
            "Line": i,
            "RawText": conversation_str,
            "SegmentSpeaker": speaker,
            "DisplayText": chat,
        }

        if content_type != "text/plain":
            g = groups[i]
            speaker = g[0].split('[', 1)[1].split(']')[1].split(" ")[2].strip()
            speaker = server_constants.SPEAKERS[speaker]
            speaker_str = re.sub("[!^:(),']", "", str(speaker))
            start_time = re.findall("[0-9]+:[0-9]+:[0-9]+\.[0-9]+", string=g[0])[0].strip()
            end_time = re.findall("[0-9]+:[0-9]+:[0-9]+\.[0-9]+", string=g[-1])[1].strip()
            segment_duration = float(calc_seconds(end_time)) - float(calc_seconds(start_time))
            transcript_segment_object["SegmentStartTimeText"] = start_time
            transcript_segment_object["SegmentEndTimeText"] = end_time
            transcript_segment_object["SegmentStartTime"] = calc_seconds(start_time)
            transcript_segment_object["SegmentEndTime"] = calc_seconds(end_time)
            transcript_segment_object["SegmentDuration"] = segment_duration
            total_duration = float(calc_seconds(end_time))
            if speaker_str == "Customer":
                customer_duration += segment_duration
            else:
                agent_duration += segment_duration

        sentiment = sentiment_object.get(i, {})
        if "Sentiment" in sentiment:
            sentiment = sentiment_object[i]["Sentiment"]
            sentiment_list.append(sentiment_object[i])
            transcript_segment_object["BaseSentiment"] = sentiment
            transcript_segment_object["BaseSentimentScores"] = sentiment_object[i][
                "SentimentScore"
            ]
        else:
            transcript_segment_object["BaseSentiment"] = None
            transcript_segment_object["BaseSentimentScores"] = []

        entities = entities_object.get(i, {})
        if "Entities" in entities and (len(entities) > 0):
            entities = entities_object[i]["Entities"]
            entities_list.append(entities_object[i])
            transcript_segment_object["EntitiesDetected"] = entities
        else:
            transcript_segment_object["EntitiesDetected"] = []

        if language != "en" and language != "original":
            translated_conversation_str = str(translated_conversation_dict[i]).strip()
            translated_conversation_split = translated_conversation_str.split(":", 1)
            translated_chat = translated_conversation_split[1].strip()
            transcript_segment_object["RawTranslatedText"] = translated_conversation_str
            transcript_segment_object["TranslatedText"] = translated_chat

        transcript_speech_segments.append(transcript_segment_object)

    transcript_json = dict()
    conversation_analytics_json = dict()
    conversation_analytics_json["SourceInformation"] = dict()
    conversation_analytics_json["SourceInformation"]["TranscribeJobInfo"] = dict()
    conversation_analytics_json["Summary"] = dict()
    payload = dict()
    payload["objectKey"] = key

    transcript_json["RawTranscript"] = temp_transcription_file_lines
    if language != "original" and language != "en":
        transcript_json["TranslatedTranscript"] = temp_translation_file_lines

    conversation_analytics_json["SourceInformation"]["Key"] = key
    conversation_analytics_json["SourceInformation"]["Bucket"] = s3_bucket

    payload["key"] = key
    payload["bucket"] = s3_bucket

    payload["summary"] = str(summarization_result).strip()
    conversation_analytics_json["Summary"]["Summary"] = payload["summary"]

    payload["actionItem"] = str(action_items).strip()
    conversation_analytics_json["Summary"]["Actions"] = payload["actionItem"]

    payload["topic"] = str(topic).strip()
    conversation_analytics_json["Summary"]["Topic"] = payload["topic"]

    payload["politeness"] = str(politeness).strip()
    conversation_analytics_json["Summary"]["Politeness"] = payload["politeness"]

    payload["callbackValue"] = str(callback_value).strip()
    conversation_analytics_json["Summary"]["Callback"] = payload["callbackValue"]

    payload["product"] = str(product).strip()
    conversation_analytics_json["Summary"]["Product"] = payload["product"]

    payload["resolution"] = str(resolution).strip()
    conversation_analytics_json["Summary"]["Resolved"] = payload["resolution"]

    payload["agentSentiment"] = str(agent_sentiment).strip()
    conversation_analytics_json["Summary"]["AgentSentiment"] = payload["agentSentiment"]

    payload["customerSentiment"] = str(customer_sentiment).strip()
    conversation_analytics_json["Summary"]["CustomerSentiment"] = payload["customerSentiment"]

    payload["dominantLanguage"] = str(dominant_language).strip()
    conversation_analytics_json["Language"] = payload["dominantLanguage"]

    payload["dominantLanguageCode"] = str(language).strip()
    conversation_analytics_json["LanguageCode"] = payload["dominantLanguageCode"]

    if content_type != "text/plain":
        ctx = Context(prec=38)
        payload["customerDuration"] = ctx.create_decimal_from_float(customer_duration)
        payload["agentDuration"] = ctx.create_decimal_from_float(agent_duration)
        payload["totalDuration"] = ctx.create_decimal_from_float(total_duration)
        conversation_analytics_json["SpeakerTime"] = {
            "Agent": {
                "TotalTimeSecs": payload["agentDuration"],
            },
            "Customer": {
                "TotalTimeSecs": payload["customerDuration"],
            },
            "Total": {
                "TotalTimeSecs": payload["totalDuration"],
            }
        }

    # Getting values from DDB and Updating
    object_from_table = table.get_item(
        Key={"objectKey": key},
        ConsistentRead=True,
    )
    if "Item" in object_from_table:
        item = object_from_table["Item"]
        payload["bucketName"] = s3_bucket
        payload["lastModified"] = item["lastModified"]
        payload["contentType"] = item["contentType"]
        payload["contentLength"] = item["contentLength"]
        payload["executionArn"] = item["executionArn"]
        payload["executionStartedAt"] = item["executionStartedAt"]
        payload["executionCompletedAt"] = datetime.now().isoformat()

        source_info_obj = dict()
        source_info_obj["LastModified"] = item["lastModified"]
        source_info_obj["ContentType"] = item["contentType"]
        source_info_obj["ContentLength"] = item["contentLength"]
        source_info_obj["ExecutionArn"] = item["executionArn"]
        source_info_obj["ExecutionStartedAt"] = item["executionStartedAt"]
        source_info_obj["ExecutionCompletedAt"] = payload["executionCompletedAt"]

        conversation_analytics_json["SourceInformation"][
            "TranscribeJobInfo"
        ] = source_info_obj

    temp_entity_map = dict()
    for entity in entities_list:
        if len(entity['Entities']) > 0:
            entries = entity['Entities']
            entity_type = entries[0]["Type"]
            entity_text = entries[0]["Text"]
            if entity_type not in temp_entity_map:
                temp_entity_map[entity_type] = []
            temp_entity_map[entity_type].append(entity_text)

    entity_map = []
    for key in temp_entity_map:
        entity_map.append({
            "Name": key,
            "Values": temp_entity_map[key],
            "Instances": len(temp_entity_map[key])
        })
    conversation_analytics_json["CustomEntities"] = entity_map

    transcript_json["SpeechSegments"] = transcript_speech_segments
    transcript_json["ConversationAnalytics"] = conversation_analytics_json

    output_file = f"{output_key}/{input_file}.json"
    sentiment_output_file = f"{output_key}/sentiment.json"
    entities_output_file = f"{output_key}/entities.json"
    entities_local = "/tmp/entities.json"
    sentiment_local = "/tmp/sentiment.json"

    payload["outputFile"] = output_file
    json_file_name = "/tmp/" + input_file + ".json"

    with open(sentiment_local, "w", encoding="utf-8") as f:
        json.dump(sentiment_list, f, ensure_ascii=False, indent=4)
    s3_client.upload_file(sentiment_local, s3_bucket, sentiment_output_file)

    with open(entities_local, "w", encoding="utf-8") as f:
        json.dump(entities_list, f, ensure_ascii=False, indent=4)
    s3_client.upload_file(entities_local, s3_bucket, entities_output_file)

    with open(json_file_name, "w", encoding="utf-8") as f:
        json.dump(transcript_json, f, ensure_ascii=False, indent=4, cls=DecimalEncoder)
    s3_client.upload_file(json_file_name, s3_bucket, output_file)

    if "Item" in object_from_table:
        table.put_item(Item=payload)
        print(f"Updated values for {key} in DDB ")

    print(f"Processed {output_key}/{input_file}.json")
    event["processed_file"] = f"{output_key}/{input_file}.json"
    return {
        "event": event,
        "status": "SUCCEEDED",
    }
