/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import React, { useState } from 'react';
import { Button, Cards, SpaceBetween, Header, Box, Modal, FormField, Input, Flashbar, Textarea } from "@cloudscape-design/components";
import { CIAPI } from '../../common';

const GroupView = ({ userid, isLoading, itemData, loadData }) => {
    const [groupModalVisible, setGroupModalVisible] = useState(false);
    const [groupTitle, setGroupTitle] = useState("");
    const [groupDescription, setGroupDescription] = useState("");
    const [selectedId, setSelectedId] = useState("");
    const [actionInProgress, setActionInProgress] = useState(false);
    const [modalTitle, setModalTitle] = useState("Add New Workflow");

    const savePrompt = async () => {
        setActionInProgress(true);
        if (selectedId !== "") {
            await CIAPI.customPromptsAPI('update', {
                section: "GROUP",
                userid: userid,
                id: selectedId,
                title: groupTitle,
                description: groupDescription
            });
        } else {
            await CIAPI.customPromptsAPI('add', {
                section: "GROUP",
                userid: userid,
                title: groupTitle,
                description: groupDescription
            });
        }
        setActionInProgress(false);
        setGroupModalVisible(false);
        setGroupTitle("");
        setGroupDescription("");
        setSelectedId("");
        loadData();
    }

    const openModal = (flag) => {
        setModalTitle("Add New Workflow");
        setGroupTitle("");
        setGroupDescription("");
        setSelectedId("");
        setGroupModalVisible(flag)
    }
    const editPromptGroup = (d) => {
        setModalTitle("Edit Workflow");
        setSelectedId(d.id)
        setGroupTitle(d.name);
        setGroupDescription(d.description);
        setGroupModalVisible(true);
    }

    const deleteAction = async (d) => {
        if (window.confirm(`Do you want to delete ${d.name} Workflow`)) {
            setActionInProgress(true);
            await CIAPI.customPromptsAPI('delete', {
                section: "GROUP",
                userid: userid,
                id: d.id
            });
            setActionInProgress(false);
            setGroupTitle("");
            setGroupDescription("");
            setSelectedId("");
            loadData();
        }
    }
    return (
        isLoading ? (<><Flashbar items={[{ loading: true, dismissible: false, content: ("Loading Workflows"), id: "message_1" }]} /></>) : (<>
            <Cards
                variant="box"
                cardDefinition={{
                    header: item => {
                        let elements = [];
                        elements.push(<Button key={`${item.id}_link`} href={`/admin/prompt/${item.id}`} variant="inline-link"> {item.name} </Button>);
                        if (item.id !== "default") {
                            elements.push(<div key={`${item.id}_promptactions`} className='promptActionItems'>
                                <Button key={`${item.id}_edit`} iconName="edit" variant="icon" onClick={() => { editPromptGroup(item) }} />
                                <Button key={`${item.id}_remove`} iconName="remove" variant="icon" onClick={() => { deleteAction(item) }} />
                            </div>);
                        }
                        return elements;
                    },
                    sections: [
                        {
                            id: "description",
                            header: "",
                            content: item => item.description
                        },
                        {
                            id: "tags",
                            header: "",
                            content: item => item.tags
                        }
                    ]
                }}

                items={itemData}
                header={
                    <Header
                        actions={
                            <SpaceBetween
                                direction="horizontal"
                                size="xs"
                            >
                                <Button variant="primary" onClick={() => openModal(true)}>New Workflow</Button>
                            </SpaceBetween>
                        }
                    >
                    </Header>
                }
            />
            <Modal
                id='modal_group'
                visible={groupModalVisible}
                dismissible={false}
                footer={
                    <Box float="right">
                        <SpaceBetween direction="horizontal" size="xs">
                            <Button variant="link" disabled={actionInProgress} onClick={() => openModal(false)}>Cancel</Button>
                            <Button variant="primary" disabled={actionInProgress} onClick={() => savePrompt()}>Save</Button>
                        </SpaceBetween>
                    </Box>
                }
                header={modalTitle}
            >
                <FormField label="Title"    >
                    <Input value={groupTitle} onChange={event => setGroupTitle(event.detail.value)} placeholder='Workflow Title' />
                </FormField>
                <FormField label="Description">
                    <Textarea onChange={({ detail }) => setGroupDescription(detail.value)} value={groupDescription} placeholder="Workflow Description" />
                </FormField>
            </Modal>
        </>)
    );
}

export default GroupView;