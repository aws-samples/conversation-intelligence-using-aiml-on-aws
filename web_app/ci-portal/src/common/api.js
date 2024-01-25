/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { API } from 'aws-amplify';

const CIAPI = {

    async getConvList() {
        const apiName = 'ci-api';
        const path = '/list';
        return await API.post(apiName, path);
    },

    async getConvDetails(key) {
        const apiName = 'ci-api';
        const path = `/details/${key}`;
        return await API.post(apiName, path);
    },

    async genAiQuery(key, query) {
        const apiName = 'ci-api';
        const path = `/genai/${key}`;
        return await API.post(apiName, path, {
            body: {
                query: query
            }
        });
    },

    async getDefaultPrompts(){
        const apiName = 'ci-api';
        const path = '/prompts/get';
        return await API.post(apiName, path);
    },

    async updateDefaultPrompts(query){
        const apiName = 'ci-api';
        const path = '/prompts/update';
        return await API.post(apiName, path,{
            body: query
        });
    },

    async customPromptsAPI(action, data){
        const apiName = 'ci-api';
        const path = `/custom/${action}`;
        return await API.post(apiName, path,{
            body: data
        });
    }
};

export default CIAPI;