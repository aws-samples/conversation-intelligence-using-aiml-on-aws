/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import React, { useState } from "react";
import { Grid, Input, ButtonDropdown } from '@cloudscape-design/components';

export const ChatInput = ({ submitQuery, wfCallback, wfData, wfLoading }) => {
  const [inputQuery, setInputQuery] = useState("");
  const onSubmit = (e) => {
    submitQuery(inputQuery);
    setInputQuery('');
    e.preventDefault();
    return true;
  }

  const onItemClick = (e) => {
    if (e.detail.id !== 'create_new_wf') {
      wfCallback(e.detail.id);
      e.preventDefault();
      return true;
    }

  }

  let dropdownItems = []
  if (wfData && wfData.data && wfData.data.grouplist.length > 0) {
    wfData.data.grouplist.forEach(element => {
      dropdownItems.push({ text: element.title, id: element.group_id });
    })
  } else {
    dropdownItems.push({
      id: "create_new_wf",
      text: "Create Workflows",
      href: "/admin",
      external: true,
      externalIconAriaLabel: "(opens in new tab)"
    });
  }

  return (

    <Grid gridDefinition={[
      { colspan: { default: 12, xxs: 8 } },
      { colspan: { default: 12, xxs: 4 } }
    ]
    }>
      <form onSubmit={onSubmit}>
        <Input
          disabled={wfLoading}
          placeholder="Enter a question about the call."
          onChange={({ detail }) => setInputQuery(detail.value)}
          value={inputQuery}
        />
      </form>

      <ButtonDropdown
        items={dropdownItems}
        mainAction={{
          text: "Submit",
          onClick: onSubmit,
          disabled: wfLoading
        }}
        variant="primary"
        onItemClick={onItemClick}
        loading={wfLoading}
        disabled={wfLoading}
      />
    </Grid>
  );
};