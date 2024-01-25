/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { FiSmile, FiMeh, FiFrown } from "react-icons/fi";

export const SentimentIcon = ({ score, size = "1.5em" }) => {
  if (score > 0) {
    return <FiSmile color="green" size={size} />;
  }

  if (score < 0) {
    return <FiFrown color="red" size={size} />;
  }

  if(typeof score === 'string' || score instanceof String){
    if(score.indexOf("Positive") > -1){
      return <FiSmile color="green" size={size} />;
    }

    if(score.indexOf("Negative") > -1 ){
      return <FiFrown color="red" size={size} />;
    }
  }

  return <FiMeh color="grey" size={size} />;
};
