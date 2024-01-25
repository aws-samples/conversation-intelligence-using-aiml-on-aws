/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import React, { useState } from 'react';
import { Grid, ContentLayout, Header, Container, SpaceBetween } from "@cloudscape-design/components";

import Layout from '../../layout';
import { Util } from '../../common';
import CustomPrompts from './Prompts';

const breadItems = [
    { text: "Home", href: "/" },
    { text: "Workflows", href: "/admin" },
]
const Admin = ({userid}) => {
    const { utilities, GenerateBreadcrum } = Util();
    const [breadcrumbItems, setBreadcrumbItems] = useState(breadItems);
    

    return (<Layout
            id="main_panel"
            navUtilities={utilities()}
            breadcrumb={GenerateBreadcrum(breadcrumbItems)}
        >
            <ContentLayout
                header={
                    <Header
                        variant="h1"
                        description="Configure your Workflows and Prompts"
                    >
                        Workflows Administration
                    </Header>
                }>
                <Grid
                    gridDefinition={[
                        { colspan: { default: 12 } }
                    ]}>
                    <Container
                        fitHeight={true}
                    >
                        <SpaceBetween size="m">
                            <CustomPrompts userid={userid} defaultBreadcrumb={breadItems} updateBreadcrumb={setBreadcrumbItems}/>
                        </SpaceBetween>
                    </Container>
                </Grid>
            </ContentLayout>
        </Layout>);
};

export default Admin;