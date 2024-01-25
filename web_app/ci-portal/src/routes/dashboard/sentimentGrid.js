/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Line } from 'react-chartjs-2';
import { colours } from "./colours";
import { Box, SpaceBetween } from '@cloudscape-design/components';

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
                    if(value === 0) return "Neutral";
                    if(value === -1) return "Negative";
                    if(value === 1) return "Positive";
                },
            }
        },
        x: {
            display: true,
            title: { text: "Call Quarter", display: true },
        }
    },
    title: {
        text: "Call Sentiment over time",
        display: true,
        position: "bottom",
    },
    plugins: {
        legend: {
            onClick: null,
            labels: {
                padding: 10,
                boxWidth: 30
            },
        },
    },
    aspectRatio: 1.2
};
const SentimentGrid = ({ data }) => {
    const labels = ["Q1", "Q2", "Q3", "Q4"];
    if (data != null) {
        let chartData = {
            labels,
            datasets: [
                {
                    label: 'Agent',
                    data: labels.map((index) => data.agent.quater[index]),
                    borderColor: colours['spk_0'],
                    backgroundColor: colours['spk_0'],
                    fill: false,
                    spanGaps: true,
                    tension: 0.5,
                },
                {
                    label: 'Customer',
                    data: labels.map((index) => data.customer.quater[index]),
                    borderColor: colours['spk_1'],
                    backgroundColor: colours['spk_1'],
                    fill: false,
                    spanGaps: true,
                    tension: 0.5,
                }
            ],
        };

        return (
            <SpaceBetween size="m">
                <Box variant="h1">Sentiment</Box>
                <Line options={options} data={chartData} />
            </SpaceBetween>)
    } else {
        return <>Coming Soon</>
    }

}


export default SentimentGrid;