/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Tag } from "../../components/Tag";
import { getEntityColor } from "./colours";
import { Tabs } from '@cloudscape-design/components';

const generateTabs = (data) => {
  let tabs = [];
  for (const e in data) {
    let keyCount = 0;
    let tags = []
    data[e].forEach(element => {
      tags.push(<Tag key={`${e}_${keyCount++}`} className="me-2 mb-1" style={{ "--highlight-colour": getEntityColor(e) }}>{ element }</Tag>);
    })
    let tab = {
      label: e,
      id: e,
      content: tags
    }
    tabs.push(tab);
  }
  return tabs;
}

export const EntityGrid = ({ data }) => {
  if(data != null) {
    return data.count !== 0 ? (
      <Tabs tabs={generateTabs(data.data)} />
    ) : (
      <p>No entities detected</p>
    );
  }
};

export default EntityGrid;