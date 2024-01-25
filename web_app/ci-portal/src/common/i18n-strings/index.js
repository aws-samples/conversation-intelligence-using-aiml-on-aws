/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

export const renderAriaLive = ({ firstIndex, lastIndex, totalItemsCount }) => `Displaying items ${firstIndex} to ${lastIndex} of ${totalItemsCount}`;

export const propertyFilterI18nStrings = {
    filteringAriaLabel: 'Find Calls',
    filteringPlaceholder: 'Find Calls',
    dismissAriaLabel: "Dismiss",
    groupValuesText: "Values",
    groupPropertiesText: "Properties",
    operatorsText: "Operators",
    operationAndText: "and",
    operationOrText: "or",
    operatorLessText: "Less than",
    operatorLessOrEqualText: "Less than or equal",
    operatorGreaterText: "Greater than",
    operatorGreaterOrEqualText: "Greater than or equal",
    operatorContainsText: "Contains",
    operatorDoesNotContainText: "Does not contain",
    operatorEqualsText: "Equals",
    operatorDoesNotEqualText: "Does not equal",
    editTokenHeader: "Edit filter",
    propertyText: "Property",
    operatorText: "Operator",
    valueText: "Value",
    cancelActionText: "Cancel",
    applyActionText: "Apply",
    allPropertiesLabel: "All properties",
    tokenLimitShowMore: "Show more",
    tokenLimitShowFewer: "Show fewer",
    clearFiltersText: "Clear filters",
};

export const baseTableAriaLabels = {
    allItemsSelectionLabel: () => 'select all',
};

const baseEditableLabels = {
    activateEditLabel: (column, item) => `Edit ${item.id} ${column.header}`,
    cancelEditLabel: column => `Cancel editing ${column.header}`,
    submitEditLabel: column => `Submit edit ${column.header}`,
};

export const distributionTableAriaLabels = {
    ...baseTableAriaLabels,
    itemSelectionLabel: (data, row) => `select ${row.id}`,
    selectionGroupLabel: 'Call selection',
};

export const distributionEditableTableAriaLabels = {
    ...distributionTableAriaLabels,
    ...baseEditableLabels,
};

export function createTableSortLabelFn(column) {
    if (!column.sortingField && !column.sortingComparator && !column.ariaLabel) {
        return;
    }
    return ({ sorted, descending }) => {
        return `${column.header}, ${sorted ? `sorted ${descending ? 'descending' : 'ascending'}` : 'not sorted'}.`;
    };
}

export const getTextFilterCounterServerSideText = (items = [], pagesCount, pageSize) => {
    const count = pagesCount > 1 ? `${pageSize * (pagesCount - 1)}+` : items.length + '';
    return count === '1' ? `1 match` : `${count} matches`;
};

export const getTextFilterCounterText = (count) => `${count} ${count === 1 ? 'match' : 'matches'}`;