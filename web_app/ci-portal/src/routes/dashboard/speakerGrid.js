/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Bar } from 'react-chartjs-2';
import { Box, SpaceBetween } from '@cloudscape-design/components';
import { colours } from "./colours";
import { Formatter } from "../../format";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);
const SpeakerTimeGrid = ({ data }) => {

    let customData = [];

    let agent = {
        channel: 'spk_0',
        label: 'Agent',
        value: data.agent.totalTime
    }

    let customer = {
        channel: 'spk_1',
        label: 'Customer',
        value: data.customer.totalTime
    }

    customData.push(agent);
    customData.push(customer);

    if (customData != null) {
        const options = {
            aspectRatio: 1.5,
            scales: {
                y: {
                    stacked: true,
                    ticks: {
                        beginAtZero: true,
                        callback: (value, index) => `${Formatter.Percentage(value)}`,
                    },
                },
                x: {
                    stacked: true,
                    display: false,
                },
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (context) =>
                            `${context.dataset.label} ${Formatter.Percentage(
                                context.parsed.y
                            )}`,
                    },
                },
                legend: {
                    onClick: null,
                    labels: {
                        padding: 10,
                        boxWidth: 15
                    },
                },
            },
        };

        const totalTime = Math.ceil(customData.reduce((prev, curr) => curr.value + prev, 0));

        return (
            <SpaceBetween size="m">
                <Box variant="h1">Speaker Time</Box>
                <Bar
                    data={{
                        labels: ["Proportion speaking"],
                        datasets: customData.map((entry) => ({
                            label: entry.label,
                            data: [entry.value / totalTime],
                            backgroundColor: colours[entry.channel],
                        })),
                    }}
                    options={options}
                ></Bar>
            </SpaceBetween>
        )
    } else {
        return <>Coming Soon</>
    }

}


export default SpeakerTimeGrid;