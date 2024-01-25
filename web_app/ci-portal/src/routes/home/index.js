/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import React, { useEffect, useState } from 'react'
import { Grid, ContentLayout, Link, Header } from "@cloudscape-design/components";

import Layout from '../../layout';
import { CIAPI, Util } from '../../common';
import { CallTable } from '../../components/CallTable';

const processData = (data) => {
    let processData = [];
    data.forEach(element => {
        element['executionDateObj'] = new Date(Date.parse(element.executionStartedAt));
        processData.push(element);
    });
    return processData;
}
const Home = () => {
    const { authStatus, utilities, GenerateBreadcrum } = Util();

    const [loading, setLoading] = useState(true);
    const [conversationList, setConversationList] = useState([]);

    const breadItems = [
        { text: "Home", href: "../" },
        { text: "Call List", href: "#" },
    ]

    useEffect(() => {
        if (authStatus === "authenticated") {
            const init = async () => {
                let apiListData = await CIAPI.getConvList();
                setConversationList(processData(apiListData));
                setLoading(false);
            }
            init();
        }
    }, [authStatus])

    return (<>
        <Layout
            id="main_panel"
            navUtilities={utilities()}
            breadcrumb={GenerateBreadcrum(breadItems)}
        >
            <ContentLayout
                header={
                    <Header
                        variant="h1"
                        description="Select a call record to view details."
                        info={<Link variant="info" ariaLabel="Info goes here.">Info</Link>}>
                        Call List
                    </Header>
                }>
                <Grid
                    gridDefinition={[
                        { colspan: { default: 12 } },
                        { colspan: { default: 12 } }
                    ]}>
                    <CallTable data={conversationList} loading={loading} />
                </Grid>
            </ContentLayout>
        </Layout>
    </>);
};

export default Home;