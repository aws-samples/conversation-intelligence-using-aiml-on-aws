/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { useState, useEffect, useRef } from "react";
import { useParams } from "react-router";
import { ContentLayout, Header, Grid, Container, SpaceBetween, Flashbar, Spinner, Button, Link } from '@cloudscape-design/components';

import Layout from '../../layout';
import { CIAPI, Util } from '../../common';
import { ValueWithLabel } from "../../components/ValueWithLabel";
import { ChatInput } from "../../components/ChatInput";
import EntityGrid from "./entityGrid";
import SentimentGrid from "./sentimentGrid";
import SpeakerTimeGrid from "./speakerGrid";
import ComprehendSentimentChart from "./comprehendSentiment";
import TranscriptGrid from "./transcript";
import DataGenerator from "./dataGenerator";

const breadItems = [
    { text: "Home", href: "../../" },
    { text: "Call List", href: "../../" },
    { text: "Call Details", href: "#" },
]

const Dashboard = ({ userid }) => {

    const { authStatus, utilities, GenerateBreadcrum } = Util();
    const { key } = useParams();
    const audioElem = useRef();
    const transcriptElem = useRef();

    const [showTranslatedTranscript, setShowTranslatedTranscript] = useState(null)
    const [insightData, setInsightData] = useState(null)
    const [entityData, setEntityData] = useState(null);
    const [sentimentData, setSentimentData] = useState(null);
    const [callmetaData, setCallmetaData] = useState(null);
    const [transcriptData, setTranscriptData] = useState(null);
    const [mediaData, setMediaData] = useState(null);
    const [callLanguage, setCallLanguage] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [genAiQueries, setGenAiQueries] = useState([]);
    const [genAiQueryStatus, setGenAiQueryStatus] = useState(false);
    const [customPrompt, setCustomPrompt] = useState(null);

    useEffect(() => {
        if (authStatus === "authenticated") {
            const init = async () => {
                let customPromptData = await CIAPI.customPromptsAPI('get', { section: "GROUP", userid: userid });
                setCustomPrompt(customPromptData)
                let apiData = await CIAPI.getConvDetails(key);
                let dashboardData = (new DataGenerator(apiData));

                setIsLoading(false);
                setEntityData(dashboardData.entityData);
                setSentimentData(dashboardData.sentimentData);
                setInsightData(dashboardData.insightData);
                setCallmetaData(dashboardData.callmetaData);
                setTranscriptData(dashboardData.transcriptData);
                setMediaData(dashboardData.media);
                setCallLanguage(dashboardData.language);
                setShowTranslatedTranscript(false);
            }
            init();
        }
    }, [authStatus, key, userid]);

    const onAudioPlayTimeUpdate = (e) => {
        let elementEndTime = undefined;
        for (let i = 0; i < transcriptData.length; i++) {
            if (audioElem.current.currentTime < transcriptData[i].endTime) {
                elementEndTime = transcriptData[i].endTime;
                break;
            }
        }
        [...transcriptElem.current.getElementsByClassName('playing')].map(elem => elem.classList?.remove("playing"));
        transcriptElem.current.querySelector('span[data-end="' + elementEndTime + '"]')?.classList?.add("playing");
    }

    const toggleShowingTranslatedText = () => {
        setShowTranslatedTranscript(!showTranslatedTranscript)
    }

    const getElementByIdAsync = (id) => {
        return new Promise(resolve => {
            const getElement = () => {
                const element = document.getElementById(id);
                if (element) {
                    resolve(element);
                } else {
                    requestAnimationFrame(getElement);
                }
            };
            getElement();
        })
    }

    const scrollToBottomOfChat = () => {
        const chatDiv = document.getElementById("chatDiv");
        chatDiv.scrollTop = chatDiv.scrollHeight;
    }

    const submitQuery = async (query) => {
        if (genAiQueryStatus === true) {
            return;
        }

        setGenAiQueryStatus(true);

        let responseData = {
            type: 'manual',
            label: query,
            value: '...'
        }
        const currentQueries = genAiQueries.concat(responseData);
        setGenAiQueries(currentQueries);
        scrollToBottomOfChat();

        let query_response = await CIAPI.genAiQuery(key, query);
        const queries = currentQueries.map(query => {
            if (query.value !== '...') {
                return query;
            } else {
                return {
                    type: 'manual',
                    label: query.label,
                    value: query_response
                }
            }
        });
        setGenAiQueries(queries);
        scrollToBottomOfChat();
        setGenAiQueryStatus(false);
    }

    const submitBulkQuery = async (data) => {
        if (genAiQueryStatus === true) {
            return;
        }
        setGenAiQueryStatus(true);
        let response = await Promise.all(data.group_info_detail.promptList.map(async item => {
            try {
                let query_response = await CIAPI.genAiQuery(key, item.prompt);
                return {
                    label: item.title,
                    value: query_response
                }
            } catch (err) {
                console.log(err)
            }
        }))
        let output = [{
            type: "workflow",
            label: <Link external href={`/admin/prompt/${data.group_info[0].group_id}`}>{`${data.group_info[0].title} `}</Link>,
            value: '',
            response: response
        }]

        const queries = genAiQueries.concat(output);
        setGenAiQueries(queries);
        scrollToBottomOfChat();
        setGenAiQueryStatus(false);
    }

    const callCustomPrompts = async (item_group_id) => {
        let customGroupPromptData = await CIAPI.customPromptsAPI('get', { section: "GROUPDETAIL", userid: userid, groupid: item_group_id });
        submitBulkQuery(customGroupPromptData.data)
    }

    const renderChatContent = () => {
        let component = [];

        if (genAiQueries.length > 0) {
            let i = 0
            genAiQueries.forEach(e => {
                if (e.type === 'manual') {
                    component.push(<div className="manual_query_response" key={`manual_${i++}`}>
                        <ValueWithLabel key={i++} label={e.label}>
                            {e.value === '...' ? <div style={{ height: '30px' }}><Spinner /></div> : e.value}
                        </ValueWithLabel>
                    </div>)
                } else {
                    let individualEntry = [];
                    e.response.forEach(element => {
                        individualEntry.push(<ValueWithLabel key={i++} label={element.label}>
                            {element.value}
                        </ValueWithLabel>)
                    });

                    component.push(<div className="custom_wf_response" key={`wf_${i++}`}>
                        <SpaceBetween size="xxs">
                            <ValueWithLabel key={i++} label={e.label}></ValueWithLabel>
                            {individualEntry}
                        </SpaceBetween>
                    </div>)
                }
            });
        }
        return component;
    }

    let gridDef = [];
    let graphGridDef = [];
    if (isLoading) {
        gridDef.push({ colspan: { l: 12, m: 12, default: 12 } });
    } else {
        gridDef.push({ colspan: { l: 4, m: 4, default: 12 } });
        gridDef.push({ colspan: { l: 8, m: 8, default: 12 } });
        gridDef.push({ colspan: { l: 12, m: 12, default: 12 } });
        gridDef.push({ colspan: { l: 6, m: 6, default: 12 } });
        gridDef.push({ colspan: { l: 6, m: 6, default: 12 } });
        gridDef.push({ colspan: { l: 12, m: 12, default: 12 } });

        graphGridDef.push({ colspan: { l: 6, m: 6, default: 6 } });
        graphGridDef.push({ colspan: { l: 6, m: 6, default: 6 } });
    }

    return (
        <Layout
            id="main_panel"
            navUtilities={utilities()}
            breadcrumb={GenerateBreadcrum(breadItems)}
        >
            <ContentLayout
                header={

                    <Header
                        variant="h1"
                        actions={<></>}
                    >
                        Call Details
                    </Header>

                }>
                <Grid
                    gridDefinition={gridDef}>
                    {
                        isLoading ? (
                            <Container>
                                <SpaceBetween size="m">
                                    <Flashbar
                                        items={[
                                            {
                                                type: "success",
                                                loading: true,
                                                content: "Fetching Call Details.",
                                                id: "message_1"
                                            }
                                        ]}
                                    />
                                </SpaceBetween>
                            </Container>
                        ) : (<>
                            <Container
                                fitHeight={true}
                                header={
                                    <Header variant="h2">
                                        Call Metadata
                                    </Header>
                                }
                            >
                                <SpaceBetween size="m">
                                    {callmetaData && callmetaData.length > 0 ? callmetaData.map((entry, i) => (
                                        <ValueWithLabel key={i} label={entry.key}>
                                            {entry.value}
                                        </ValueWithLabel>
                                    )) : <ValueWithLabel key='nosummary'>No Summary Available</ValueWithLabel>}
                                </SpaceBetween>
                            </Container>

                            <Container fitHeight={true}>
                                <SpaceBetween direction="vertical" size="l">
                                    <Grid gridDefinition={graphGridDef}>
                                        <SentimentGrid data={sentimentData} />
                                        <SpeakerTimeGrid data={sentimentData} />
                                    </Grid>
                                    <SpaceBetween size="m" >
                                        <ComprehendSentimentChart data={sentimentData} />
                                    </SpaceBetween>
                                </SpaceBetween>
                            </Container>

                            <Container
                                fitHeight={true}
                                header={<Header variant="h2">Entities</Header>} >
                                <EntityGrid data={entityData} />
                            </Container>

                            <Container
                                fitHeight={true}
                                header={<Header variant="h2"> Insights </Header>}>
                                <SpaceBetween size="m">
                                    {insightData && insightData.length > 0 ? insightData.map((entry, i) => (
                                        <ValueWithLabel key={i} label={entry.key}>
                                            {entry.value}
                                        </ValueWithLabel>
                                    )) : <ValueWithLabel key='nosummary'>No Summary Available</ValueWithLabel>}
                                </SpaceBetween>
                            </Container>
                            <Container
                                fitHeight={true}
                                header={
                                    <Header
                                        variant="h2"
                                        description="Ask a question below or select workflow">Analysis</Header>
                                }
                                footer={
                                    <SpaceBetween size="m">
                                        <ChatInput submitQuery={submitQuery} wfCallback={callCustomPrompts} wfData={customPrompt} wfLoading={genAiQueryStatus} />
                                    </SpaceBetween>}>
                                <div id="chatDiv" style={{ overflow: "hidden", overflowY: 'auto', height: '30em' }}>
                                    <SpaceBetween size="m">
                                        {renderChatContent()}
                                    </SpaceBetween>
                                </div>
                            </Container>

                            <Container
                                header={
                                    <Header
                                        variant="h2"
                                        actions={<SpaceBetween
                                            direction="horizontal"
                                            size="xs">
                                            <Button disabled={callLanguage === "english"} onClick={toggleShowingTranslatedText}>
                                                {showTranslatedTranscript ? "Show Original Transcript" : "Show Translated Transcript"}
                                            </Button>
                                            {mediaData && (
                                                <audio
                                                    key='audoiElem'
                                                    ref={audioElem}
                                                    className="float-end"
                                                    controls
                                                    src={mediaData.url}
                                                    onTimeUpdate={onAudioPlayTimeUpdate}
                                                >
                                                    Your browser does not support the
                                                    <code>audio</code> element.
                                                </audio>
                                            )}
                                        </SpaceBetween>}
                                    >
                                        Transcript {(showTranslatedTranscript ? " (Translated)" : "(Original)")}
                                    </Header>
                                }>
                                <div ref={transcriptElem}>
                                    <TranscriptGrid showTranslatedTranscript={showTranslatedTranscript} language={callLanguage} data={transcriptData} />
                                </div>

                            </Container>
                        </>)

                    }
                </Grid>
            </ContentLayout>
        </Layout>
    );
};


export default Dashboard;