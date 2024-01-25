/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import React, { useEffect, useState } from 'react';
import { useParams } from "react-router";
import { SpaceBetween, Badge, } from "@cloudscape-design/components";
import { CIAPI } from '../../common';
import GroupView from './GroupView';
import GroupDetailView from './GroupDetailView';

const CustomPrompts = ({ userid , defaultBreadcrumb , updateBreadcrumb}) => {
    const [isLoading, setIsLoading] = useState(true);
    const [groupViewData, setGroupViewData] = useState([]);

    const { key } = useParams();

    const transformAPIData = (defaultData, customData) => {
        let groupViewData = []
        groupViewData.push({
            id: "default",
            name: "Default Workflow",
            description: "This is a system defined workflow which cannot be delete but can be edited",
            tags: <SpaceBetween direction="horizontal" size="xs"><Badge color="red">Default</Badge></SpaceBetween>,
            prompts: defaultData
        })
        
        if (customData.data) {
            customData.data.grouplist.forEach(element => {
                groupViewData.push({
                    id: element.group_id,
                    name: element.title,
                    description: element.description,
                    tags: <SpaceBetween direction="horizontal" size="xs"><Badge color="blue">Custom</Badge></SpaceBetween>,
                })
            });
        }
        return groupViewData;
    }

    const loadGroupData = async () => {
        setIsLoading(true);
        let defaultPromptData = await CIAPI.getDefaultPrompts();
        let customPromptData = await CIAPI.customPromptsAPI('get', { section: "GROUP", userid: userid });
        setGroupViewData(transformAPIData(defaultPromptData, customPromptData));
        setIsLoading(false);
    }

    useEffect(() => {
        const init = async () => {
            if (key === undefined) {
                updateBreadcrumb(defaultBreadcrumb)
                await loadGroupData()
            }
        }
        init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [key])

    

    return (
        <>
            {
                !key && <GroupView userid={userid} isLoading={isLoading} itemData={groupViewData} loadData={loadGroupData}/>
            }
            {
                key && <GroupDetailView userid={userid} groupid={key} defaultBreadcrumb={defaultBreadcrumb} updateBreadcrumb={updateBreadcrumb}/>
            }
        </>
    );
}

export default CustomPrompts;