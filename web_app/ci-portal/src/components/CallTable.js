/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import * as React from "react";
import { useCollection } from '@cloudscape-design/collection-hooks';
import { Table, PropertyFilter, Pagination } from "@cloudscape-design/components";
import {
  distributionTableAriaLabels,
  getTextFilterCounterText,
  propertyFilterI18nStrings,
  renderAriaLive,
} from '../common/i18n-strings';

import { COLUMN_DEFINITIONS, FILTERING_PROPERTIES } from "./TableConfig";

export const CallTable = ({ data, loading }) => {
  const { items, filteredItemsCount, collectionProps, paginationProps, propertyFilterProps } = useCollection(
    data,
    {
      propertyFiltering: {
        filteringProperties: FILTERING_PROPERTIES,
        empty: (
          <div>No Conversations</div>
        ),
        noMatch: (
          <div>No matches.</div>
        )
      },
      pagination: { pageSize: 15 },
      sorting: {},
      selection: {},
    }
  );

  return (
    <Table
      {...collectionProps}
      items={items}
      columnDefinitions={COLUMN_DEFINITIONS}
      ariaLabels={distributionTableAriaLabels}
      renderAriaLive={renderAriaLive}
      stickyHeader={true}
      resizableColumns={true}
      wrapLines={false}
      stripedRows={true}
      contentDensity={"comfortable"}
      stickyColumns={{ first: 2, last: 0 }}
      onColumnWidthsChange={(e) => { console.log(e) }}
      loading={loading}
      loadingText="Loading Calls Information"
      filter={
        <PropertyFilter
          {...propertyFilterProps}
          i18nStrings={propertyFilterI18nStrings}
          countText={getTextFilterCounterText(filteredItemsCount)}
          expandToViewport={true}
        />
      }
      pagination={<Pagination {...paginationProps} />}

    />
  )
}