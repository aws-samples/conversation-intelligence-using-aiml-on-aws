/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import React, { useEffect, useState } from 'react';
import { Button, Grid, SpaceBetween, Box, Header, Table, Popover, Flashbar, Modal, FormField, Input, Textarea } from "@cloudscape-design/components";
import { CIAPI } from '../../common';

function generate_uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,
        function (c) {
            // eslint-disable-next-line no-unused-vars, no-mixed-operators
            var uuid = Math.random() * 16 | 0, v = c === 'x' ? uuid : (uuid & 0x3 | 0x8);
            return uuid.toString(16);
        });
}
const GroupDetailView = ({ userid, groupid, defaultBreadcrumb , updateBreadcrumb }) => {
    const [isLoading, setIsLoading] = useState(true);
    const [selectedId, setSelectedId] = useState("");
    const [isNoData, setIsNoData] = useState(false);
    const [promptList, setPromptList] = useState([]);
    const [promptGroupTitle, setPromptGroupTitle] = useState("");
    const [promptInfo, setPromptInfo] = useState("");
    const [promptModalVisible, setPromptModalVisible] = useState(false);
    const [promptTitle, setPromptTitle] = useState("");
    const [promptText, setPromptText] = useState("");
    const [addPromptDisable, setAddPromptDisable] = useState(false)
    useEffect(() => {
        const init = async () => {
            const newBreadCrumb = JSON.parse(JSON.stringify(defaultBreadcrumb));
            newBreadCrumb.push({text: '...', href: '#'})
            updateBreadcrumb(newBreadCrumb)

            if (groupid === "default") {
                setAddPromptDisable(true);
                await refreshDefaultPromptList();
            } else {
                await refreshPromptList();
            }
            setIsLoading(false);
        }
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userid, groupid])

    const refreshDefaultPromptList = async () => {
        let defaultPromptData = await CIAPI.getDefaultPrompts();
        const DEFAULT_TITLE = "Default Prompts";
        setPromptGroupTitle(DEFAULT_TITLE)
        defaultPromptData.forEach(element => {
            element['prompt_id'] = generate_uuidv4()
        })
        setPromptList(defaultPromptData)
        const newBreadCrumb = JSON.parse(JSON.stringify(defaultBreadcrumb));
        newBreadCrumb.push({text: DEFAULT_TITLE, href: '#'})
        updateBreadcrumb(newBreadCrumb)
    }

    const refreshPromptList = async () => {
        let customGroupPromptData = await CIAPI.customPromptsAPI('get', { section: "GROUPDETAIL", userid: userid, groupid: groupid });
        if (customGroupPromptData.data !== null && customGroupPromptData.data.group_info.length === 1) {
            setPromptList(customGroupPromptData.data.group_info_detail.promptList);
            setPromptGroupTitle(customGroupPromptData.data.group_info[0].title)
            let updateDate = new Date(customGroupPromptData.data.group_info_detail.created_on * 1000);
            if (customGroupPromptData.data.group_info_detail.promptList && customGroupPromptData.data.group_info_detail.promptList.length >= 10)
                setAddPromptDisable(true);
            else
                setAddPromptDisable(false);
            if (customGroupPromptData.data.group_info[0].current_version !== '0')
                setPromptInfo(<>
                    <span className='prompt_info'>Current version </span>
                    <span className='prompt_info prompt_info_message'>v{customGroupPromptData.data.group_info[0].current_version}</span>
                    <span className='prompt_info'> Last updated on </span>
                    <span className='prompt_info prompt_info_message'>{updateDate.toLocaleString()}</span>
                </>)
        } else {
            setIsNoData(true)
        }
        const newBreadCrumb = JSON.parse(JSON.stringify(defaultBreadcrumb));
        newBreadCrumb.push({text: customGroupPromptData.data.group_info[0].title, href: '#'})
        updateBreadcrumb(newBreadCrumb)
    }

    const saveGroupDetail = async () => {
        setIsLoading(true);
        if (groupid === "default") {
            await CIAPI.updateDefaultPrompts({
                "title": promptTitle,
                "prompt": promptText,
            });
            refreshDefaultPromptList();
        } else {
            let tempPromptList = [];
            if (selectedId === "") {
                tempPromptList = promptList ? [...promptList] : [];
                tempPromptList.push({
                    "prompt_id": generate_uuidv4(),
                    "title": promptTitle,
                    "prompt": promptText,
                });
            } else {
                promptList.forEach(element => {
                    if (element.prompt_id === selectedId) {
                        element.title = promptTitle;
                        element.prompt = promptText;
                    }
                    tempPromptList.push(element);
                });
            }

            await CIAPI.customPromptsAPI('add', {
                section: "GROUPDETAIL",
                userid: userid,
                groupid: groupid,
                promptlist: tempPromptList
            });
            await refreshPromptList();
        }
        setIsLoading(false);
        setPromptModalVisible(false);
        setPromptText("");
        setPromptTitle("");
        setSelectedId("");
    }

    const deletePrompt = async (id) => {
        if (window.confirm("Are you sure to delete the prompt")) {
            setIsLoading(true);
            let tempPromptList = [];
            promptList.forEach(element => {
                if (element.prompt_id !== id) {
                    tempPromptList.push(element)
                }
            });
            await CIAPI.customPromptsAPI('add', {
                section: "GROUPDETAIL",
                userid: userid,
                groupid: groupid,
                promptlist: tempPromptList
            });
            await refreshPromptList();
            setIsLoading(false);
        }
    }

    const openModal = (id) => {
        if (id == null) {
            setPromptModalVisible(true);
        } else {
            promptList.forEach(element => {
                if (element.prompt_id === id) {
                    setSelectedId(id);
                    setPromptTitle(element.title);
                    setPromptText(element.prompt);
                }
            });
            setPromptModalVisible(true);
        }
    }
    
    const renderLoading = () => {
        return (<Flashbar items={[{ loading: true, dismissible: false, content: ("Loading Workflow Details"), id: "message_1" }]} />);
    }
    const renderGrid = () => {
        return (<><Grid
            gridDefinition={[
                { colspan: { default: 12 } }
            ]}>
            <SpaceBetween size="m">
                <Header
                    actions={
                        <SpaceBetween direction="horizontal" size="xs">
                            <Button variant='primary' onClick={() => { openModal(null) }} disabled={addPromptDisable}>Add New Prompt</Button>
                            <Button href="/admin" variant="link">Back</Button>
                        </SpaceBetween>
                    }
                    info={<>{promptInfo}<SpaceBetween>
                        <span className='promptInfo'>A workflow is limited to a maximum of 10 prompts</span>
                        
                    </SpaceBetween></>}>{promptGroupTitle}</Header>

                <Box>
                    <Table
                        variant='box'
                        columnDefinitions={[
                            {
                                id: "title",
                                header: "Title",
                                cell: item => (item.title),
                                sortingField: "title",
                                isRowHeader: true
                            },
                            {
                                id: "prompt",
                                header: "Prompt",
                                cell: item => {
                                    if (item.prompt !== undefined) {
                                        return (
                                            <Popover
                                                dismissButton={false}
                                                position="top"
                                                size="large"
                                                triggerType="text"
                                                content={item.prompt.replace("/<question>[\\s\\S]*?<\\/question>/gm", "")}
                                            >
                                                {(item.prompt.length > 20 ? item.prompt.substring(0, 250) + "..." : item.prompt.replace("/<question>[\\s\\S]*?<\\/question>/gm", ""))}
                                            </Popover>
                                        )
                                    }
                                    return 'n/a'
                                },
                                maxWidth: 350,
                            },
                            {
                                id: "actions",
                                header: "Actions",
                                cell: item => {
                                    return (
                                        <SpaceBetween direction="horizontal" size="xs">
                                            <Button key={`${item.prompt_id}_edit`} onClick={() => openModal(item.prompt_id)} iconName="edit" variant="icon" />
                                            <Button key={`${item.prompt_id}_remove`} onClick={() => deletePrompt(item.prompt_id)} iconName="remove" disabled={groupid === "default"} variant="icon" />
                                        </SpaceBetween>
                                    )
                                }
                            }
                        ]}
                        items={promptList}
                        empty={
                            <Box
                                margin={{ vertical: "xs" }}
                                textAlign="center"
                                color="inherit"
                            >
                                <SpaceBetween size="m">
                                    <b>No Prompts Available</b>
                                </SpaceBetween>
                            </Box>
                        }
                    />
                </Box>
            </SpaceBetween>
        </Grid>
            <Modal
                id='modal_group_Detail'
                visible={promptModalVisible}
                footer={
                    <Box float="right">
                        <SpaceBetween direction="horizontal" size="xs">
                            <Button variant="link" disabled={isLoading} onClick={() => setPromptModalVisible(false)}>Cancel</Button>
                            <Button variant="primary" disabled={isLoading} onClick={() => saveGroupDetail()}>Save</Button>
                        </SpaceBetween>
                    </Box>
                }
                header="Prompts"
            >
                <FormField label="Prompt Title"    >
                    <Input value={promptTitle} onChange={event => setPromptTitle(event.detail.value)} placeholder='Prompt Title' disabled={groupid === "default"} />
                </FormField>
                <FormField label="Prompt Text">
                    <Textarea onChange={({ detail }) => setPromptText(detail.value)} value={promptText} placeholder="Prompt Text" rows={20}/>
                </FormField>
            </Modal>
        </>);
    }
    const renderComponent = () => {
        let component = null;
        if (isLoading) {
            component = renderLoading();
        }
        else if (!isNoData) {
            component = renderGrid();
        } else { component = <>Wrong Info</> }
        return component;
    }
    return (renderComponent())
}

export default GroupDetailView;