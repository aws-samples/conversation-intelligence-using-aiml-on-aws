/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { createTableSortLabelFn } from "../common/i18n-strings";
import { Popover, Link } from "@cloudscape-design/components";
import { SentimentIcon } from "./SentimentIcon";
import { Formatter } from "../format";
import { DateTimeForm, formatDateTime } from './DateTimeForm';

const rawColumns = [
    {
        id: "executionDateObj",
        sortingField: "executionDateObj",
        header: "Timestamp",
        cell: e => <Link variant="primary" href={`/dashboard/${e.objectKey}`}>{Formatter.Timestamp(Date.parse(e.executionStartedAt))}</Link>,
        minWidth: 170
    },
    {
        id: "objectKey",
        header: "Job Name",
        cell: e => (<Link variant="primary" href={`/dashboard/${e.objectKey}`}>{e.objectKey.replace("input/", "")}</Link>),
        minWidth: 180,
    },
    {
        id: "resolution",
        header: "Resolved",
        sortingField: "resolution",
        cell: e => e.resolution,
    },
    {
        id: "topic",
        header: "Topic",
        sortingField: "topic",
        cell: e => e.topic,

    },
    {
        id: "product",
        header: "Product",
        sortingField: "product",
        cell: e => e.product,

    },
    {
        id: "summary",
        header: "Summary",
        cell: e => {
            if (e.summary !== undefined) {
                return (
                    <Popover
                        dismissButton={false}
                        position="top"
                        size="large"
                        triggerType="text"
                        content={e.summary.replace("/<question>[\\s\\S]*?<\\/question>/gm", "")}
                    >
                        {(e.summary.length > 20 ? e.summary.substring(0, 50) + "..." : e.summary.replace("/<question>[\\s\\S]*?<\\/question>/gm", ""))}
                    </Popover>
                )
            }
            return 'n/a'
        },
        minWidth: 300,
    },
    {
        id: "customerSentiment",
        header: "Cust Sent",
        sortingField: "customerSentiment",
        cell: e => (
            <div className="d-flex justify-content-evenly">
                <SentimentIcon score={e?.customerSentiment} />
            </div>
        )
    },
    {
        id: "dominantLanguage",
        header: "Lang Code",
        sortingField: "dominantLanguage",
        cell: e => e.dominantLanguage,
    },
    {
        id: "totalDuration",
        header: "Duration",
        sortingField: "totalDuration",
        cell: e => Formatter.Time(e.totalDuration)
    }

];

export const COLUMN_DEFINITIONS = rawColumns.map(column => ({ ...column, ariaLabel: createTableSortLabelFn(column) }));

export const FILTERING_PROPERTIES = [
    {
        key: "objectKey",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Job Name",
        groupValuesLabel: "Job Name"
    },
    {
        key: "resolution",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Resolved",
        groupValuesLabel: "resolution"
    },
    {
        key: "topic",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Topic",
        groupValuesLabel: "Topics"
    },
    {
        key: "product",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Product",
        groupValuesLabel: "Products"
    },
    {
        key: "dominantLanguage",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Language Code",
        groupValuesLabel: "Languages Codes"
    },
    {
        key: "summary",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Summary",
        groupValuesLabel: "Summary"
    },
    {
        key: "customerSentiment",
        operators: ["=", "!=", ":", "!:"],
        propertyLabel: "Customer Sentiment",
        groupValuesLabel: "Customer Sentiment"
    },
    {
        key: "totalDuration",
        defaultOperator: '>',
        operators: ['<', '<=', '>', '>='],
        propertyLabel: "Duration",
        groupValuesLabel: "Durations"
    },
    {
        key: "executionDateObj",
        propertyLabel: "Timestamp",
        groupValuesLabel: "Timestamps",
        defaultOperator: '>',
        operators: ['<', '<=', '>', '>='].map(operator => ({
            operator,
            form: DateTimeForm,
            format: formatDateTime,
            match: 'datetime',
        }))

    }
].sort((a, b) => a.propertyLabel.localeCompare(b.propertyLabel));

export const DEFAULT_PREFERENCES = {
    pageSize: 30,
    wrapLines: false,
    stripedRows: true,
    contentDensity: 'comfortable',
    stickyColumns: { first: 2, last: 0 },
}