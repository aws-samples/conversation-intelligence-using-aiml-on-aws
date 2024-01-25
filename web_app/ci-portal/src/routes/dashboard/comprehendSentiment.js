/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Line } from 'react-chartjs-2';
import { colours } from "./colours";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import {Box, SpaceBetween} from "@cloudscape-design/components";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const options = {
    legend: {
        display: true,
    },
    scales: {
        y: {
            title: { text: "Sentiment", display: true },
            suggestedMin: -1,
            suggestedMax: 1,
            ticks: {
                callback: (value) => {
                    if (value === 0) return "Neutral";
                    if (value === -1) return "Negative";
                    if (value === 1) return "Positive";
                },
            }
        },
        x: {
            type: "linear",
            stacked: true,
            offset: false,
            display: true,
            position: "left",
            title: { text: "Duration", display: true },
            ticks: { callback: (value) => ( value % 10 === 0 ? value : '')}
        },
    },
    aspectRatio: 3
};

const ComprehendSentimentChart = ({ data }) => {

    if (data != null) {
        let chartData = {
            datasets: [
                {
                    label: 'Agent',
                    data: data.agent.comprehend,
                    borderColor: colours['spk_0'],
                    backgroundColor: colours['spk_0'],
                    fill: false,
                    spanGaps: true,
                    tension: 0.5,
                    pointRadius: 2,
                },
                {
                    label: 'Customer',
                    data: data.customer.comprehend,
                    borderColor: colours['spk_1'],
                    backgroundColor: colours['spk_1'],
                    fill: false,
                    spanGaps: true,
                    tension: 0.5,
                    pointRadius: 2,
                }
            ],
        };

        return (
            <SpaceBetween size="m">
                <Box variant="h1">Line by Line Sentiment</Box>
                <Line options={options} data={chartData} />
            </SpaceBetween>
        )
    } else {
        return <>Coming Soon</>
    }

}


export default ComprehendSentimentChart;