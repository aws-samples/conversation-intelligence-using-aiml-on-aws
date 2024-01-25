/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Box } from '@cloudscape-design/components';
import { SentimentIcon } from "../../components/SentimentIcon";
import { Formatter } from "../../format";

const TranscriptGrid = ({ data, language, showTranslatedTranscript }) => {
    return (<Box>
        {
            data.map((rec, i) => (
                <div id={`transcript_line_${i}`} key={`transcript_line_${i}`} style={{ display: "flex", paddingBottom: "1rem" }}>
                    <div style={{ margin: "0.4rem" }}>
                        <SentimentIcon score={rec.score} size="2em" />
                    </div>
                    <div>
                        <span className={"text-muted segment"}>
                            {`${rec.actor} - ${Formatter.Time(rec.startTime)}`}
                        </span>
                        <div>
                            <span 
                            className="highlight"
                            data-start={rec.startTime}
                            data-end={rec.endTime}
                            >
                                <span>
                                    {showTranslatedTranscript && (rec.translatedText)}
                                    {!showTranslatedTranscript && (rec.text)}
                                </span>
                            </span>
                        </div>

                    </div>
                </div>
            ))
        }
    </Box>)
}

export default TranscriptGrid;