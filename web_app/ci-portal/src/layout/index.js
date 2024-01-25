/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import AppLayout from '@cloudscape-design/components/app-layout';
import TopNavigation from '@cloudscape-design/components/top-navigation';

import './style.css';

export default function Layout({ children, contentType, tools, navUtilities, breadcrumb }) {
  return (
    <>
      <div id="top-nav">
        <TopNavigation
          identity={{
            href: '/',
            title: "Conversation Intelligence using AIML Services on AWS"
          }}
          i18nStrings={{
            overflowMenuTriggerText: 'More',
            overflowMenuTitleText: 'All',
          }}

          utilities={navUtilities}
        />
      </div>
      <AppLayout
        stickyNotifications
        contentType={contentType}
        navigation={null}
        toolsHide={true}
        navigationHide={true}
        breadcrumbs={breadcrumb}
        tools={tools}
        content={children}
        headerSelector="#top-nav"
        footerSelector="#bottom-bar"
      />
      {/*<div id="bottom-bar">*/}
      {/*  &copy; Amazon 2023 All Rights Reserved.*/}
      {/*</div>*/}
    </>
  );
}
