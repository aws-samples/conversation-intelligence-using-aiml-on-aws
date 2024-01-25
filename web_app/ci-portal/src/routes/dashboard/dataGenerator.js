/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Formatter } from "../../format";
import { Sentiment } from "../../components/Sentiment";

const sentimentValue = (txt) => {
    let val = 0;
    switch (txt) {
        case 'POSITIVE': val = 2; break;
        case 'NEGATIVE': val = -2; break;
        default: val = 0;
    }
    return val;
}

const getSentimentScore = (txt, obj) => {
    let val = 0;
    switch (txt) {
        case 'POSITIVE': val = obj.Positive; break;
        case 'NEGATIVE': val = -1 * obj.Negative; break;
        default: val = 0;
    }
    return val;
}

class DataGenerator {
    rawData = null;
    entityData = {};
    sentimentData = {
        agent: { data: [], avgSentiment: 0, avgSentimentTxt: '', quater: {}, totalTime: 0, comprehend: [] },
        customer: { data: [], avgSentiment: 0, avgSentimentTxt: '', quater: {}, totalTime: 0, comprehend: [] },
    };
    insightData = [];
    callmetaData = [];
    calltranscribeData = [];
    transcriptData = [];

    media = {
        url:""
    }

    constructor(data) {
        this.rawData = data;
        this.processData();
    }

    processData() {
        let length = 0;
        let tempEntity = {};

        let speechSegment = this.rawData.SpeechSegments;

        let agent_data_count = 0;
        let customer_data_count = 0;
        let agent_score_sum = 0;
        let customer_score_sum = 0;

        let agent_total_time = 0;
        let customer_total_time = 0;

        let agent_comprehend_sentiment = [];
        let customer_comprehend_sentiment = [];
        let record_count = 0;

        speechSegment.forEach((record) => {
            let SegmentSpeaker = record.SegmentSpeaker;


            // Processing for Sentiment
            if (SegmentSpeaker === "Agent") {
                this.sentimentData.agent.data.push(sentimentValue(record.BaseSentiment));
                agent_total_time += (record.SegmentEndTime - record.SegmentStartTime);
                agent_data_count++;
                agent_score_sum += getSentimentScore(record.BaseSentiment, record.BaseSentimentScores);
                agent_comprehend_sentiment.push({ x: record_count, y: getSentimentScore(record.BaseSentiment, record.BaseSentimentScores) })
            }


            if (SegmentSpeaker === "Customer") {
                this.sentimentData.customer.data.push(sentimentValue(record.BaseSentiment));
                customer_total_time += (record.SegmentEndTime - record.SegmentStartTime);
                customer_data_count++;
                customer_score_sum += getSentimentScore(record.BaseSentiment, record.BaseSentimentScores);
                customer_comprehend_sentiment.push({ x: record_count, y: getSentimentScore(record.BaseSentiment, record.BaseSentimentScores) })
            }


            // Processing for Entities
            record.EntitiesDetected.forEach((entity) => {
                if (tempEntity[entity.Type]) {
                    if (!tempEntity[entity.Type].includes(entity.Text)) {
                        tempEntity[entity.Type].push(entity.Text)
                    }
                } else {
                    tempEntity[entity.Type] = [entity.Text];
                    length++;
                }
            })

            // Process Transcript Data
            this.transcriptData.push({
                actor: SegmentSpeaker,
                sentiment: record.BaseSentiment,
                startTime: record.SegmentStartTime,
                endTime: record.SegmentEndTime,
                text: record.DisplayText,
                translatedText: record.TranslatedText,
                score: sentimentValue(record.BaseSentiment)
            })

            record_count++;
        });

        this.sentimentData.agent.avgSentiment = parseFloat(agent_score_sum / agent_data_count);
        this.sentimentData.customer.avgSentiment = parseFloat(customer_score_sum / customer_data_count);

        this.sentimentData.agent.totalTime = agent_total_time;
        this.sentimentData.customer.totalTime = customer_total_time;

        this.sentimentData.agent.comprehend = agent_comprehend_sentiment;
        this.sentimentData.customer.comprehend = customer_comprehend_sentiment;

        this.entityData = {
            count: length,
            data: tempEntity
        }


        // processing Generative AI Insights

        let ConversationAnalytics = this.rawData.ConversationAnalytics;

        let summary = ConversationAnalytics.Summary;

        this.insightData.push({ key: 'Summary', value: summary.Summary });
        this.insightData.push({ key: 'Topic', value: summary.Topic });
        this.insightData.push({ key: 'Product', value: summary.Product });
        this.insightData.push({ key: 'Resolved', value: summary.Resolved });
        this.insightData.push({ key: 'Callback', value: summary.Callback });
        this.insightData.push({ key: 'Politeness', value: summary.Politeness });
        this.insightData.push({ key: 'Actions', value: summary.Actions });


        // processing Call Metadata

        let metadata = ConversationAnalytics.SourceInformation;

        this.callmetaData.push({ key: 'Uploaded Time', value: `${Formatter.Timestamp(Date.parse(metadata.TranscribeJobInfo.LastModified))}` });
        this.callmetaData.push({ key: 'Call Duration', value: `${Formatter.Time(agent_total_time + customer_total_time)}` });
        this.callmetaData.push({ key: 'Language Model', value: ConversationAnalytics.Language +" ("+ConversationAnalytics.LanguageCode + ")" });
        this.callmetaData.push({ key: 'Agent Sentiment', value: (<Sentiment score={this.sentimentData.agent.avgSentiment} trend={this.sentimentData.agent.avgSentiment} />) });
        this.callmetaData.push({ key: 'Customer Sentiment', value: (<Sentiment score={this.sentimentData.customer.avgSentiment} trend={this.sentimentData.customer.avgSentiment} />) });
        this.callmetaData.push({ key: 'Type', value: 'Transcribe' });
        this.callmetaData.push({ key: 'Job Id', value: metadata.Key })
        this.callmetaData.push({ key: 'File Format', value: metadata.TranscribeJobInfo.ContentType })


        // processing Call Transcribe Details
        this.calltranscribeData.push({ key: 'Type', value: 'Transcribe' });
        this.calltranscribeData.push({ key: 'Job Id', value: metadata.Key })
        this.calltranscribeData.push({ key: 'File Format', value: metadata.TranscribeJobInfo.ContentType })
        this.calltranscribeData.push({ key: 'Sample Rate', value: '-' })
        this.calltranscribeData.push({ key: 'PII Redaction', value: '-' })
        this.calltranscribeData.push({ key: 'Custom Vocabulary', value: '-' })
        this.calltranscribeData.push({ key: 'Vocabulary Filter', value: '-' })
        this.calltranscribeData.push({ key: 'Average Word Confidence', value: '-' })

        // calculating sentiment quater for agent


        let agent_split_size = parseInt(this.sentimentData.agent.data.length / 4);
        let i = 0;
        let quater = 1;
        let quater_tot = 0;
        while (i < this.sentimentData.agent.data.length) {
            quater_tot += this.sentimentData.agent.data[i];
            if (i % agent_split_size === 0) {
                this.sentimentData.agent.quater[`Q${quater}`] = parseFloat(quater_tot / agent_split_size);
                quater++;
                quater_tot = 0
            }
            i++;
        }

        // calculating sentiment quater for customer
        let customer_split_size = parseInt(this.sentimentData.customer.data.length / 4);
        i = 0;
        quater = 1;
        quater_tot = 0;
        while (i < this.sentimentData.customer.data.length) {
            quater_tot += this.sentimentData.customer.data[i];
            if (i % customer_split_size === 0) {
                this.sentimentData.customer.quater[`Q${quater}`] = parseFloat(quater_tot / agent_split_size);
                quater++;
                quater_tot = 0
            }
            i++;
        }

        // Media Placeholder
        this.media.url = ConversationAnalytics.SourceInformation?.TranscribeJobInfo?.MediaFileUri
        this.language = ConversationAnalytics.Language
    }
}

export default DataGenerator;