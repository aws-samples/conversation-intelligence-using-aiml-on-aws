/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import "./Tag.css";

export const Tag = ({ children, className = "", ...props }) => (
  <div {...props} className={`highlight tag ${className}`}>
    {children}
  </div>
);
