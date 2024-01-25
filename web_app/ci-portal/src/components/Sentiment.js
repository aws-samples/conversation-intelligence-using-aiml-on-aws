/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { SentimentIcon } from "./SentimentIcon";

export const Sentiment = ({ score }) => {
  return (
    <span className="d-flex gap-2 align-items-center">
      <SentimentIcon score={score} />
    </span>
  );
};
