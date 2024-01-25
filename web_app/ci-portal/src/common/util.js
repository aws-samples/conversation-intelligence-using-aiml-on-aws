/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { useAuthenticator } from '@aws-amplify/ui-react';
import { BreadcrumbGroup } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';

const Util = () => {
    const { authStatus } = useAuthenticator((context) => [context.authStatus]);

    const { user, signOut } = useAuthenticator((context) => [context.user, context.signOut]);

    const navigate = useNavigate();

    function utilities() {
        const navClick = (e) => {
            // eslint-disable-next-line default-case
            switch (e.detail.id) {
                case 'home':
                    navigate('/');
                    break;
                case 'prompt_admin':
                    navigate('/admin');
                    break;
                case 'sign-out':
                    signOut();
                    navigate('/');
                    break;
            }
        };
        if (authStatus === 'authenticated' && user !== undefined) {
            return [
                {
                    type: 'menu-dropdown',
                    text: user.attributes.email,
                    iconName: 'user-profile',
                    onItemClick: (e) => {
                        navClick(e);
                    },
                    items: [
                        { id: 'home', text: 'Home' },
                        { id: 'prompt_admin', text: 'Workflows Administration' },
                        { id: 'sign-out', text: 'Sign out' },
                    ],
                },
            ];
        } else {
            return [
                {
                    type: 'menu-dropdown',
                    description: '',
                    iconName: 'user-profile',
                    onItemClick: (e) => {
                        navClick(e);
                    },
                    items: [
                        { id: 'home', text: 'Home' },
                        { id: 'term-condition', text: 'Term & Condition' },
                        { id: 'sign-in', text: 'Sign In' },
                    ],
                },
            ];
        }
    }

    function GenerateBreadcrum(list) {
        return <BreadcrumbGroup
            items={list}
            ariaLabel="Breadcrumbs"
        />
    }

    function getSentimentScore(sentimentString){
        if(sentimentString === "Positive")
            return 1;
        if(sentimentString === "Negative")
            return -1;
        return 0;
    }

    return {
        authStatus,
        user,
        signOut,
        navigate,
        utilities,
        GenerateBreadcrum,
        getSentimentScore
    };
};

export default Util;