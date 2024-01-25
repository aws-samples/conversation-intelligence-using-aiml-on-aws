/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { Box } from '@cloudscape-design/components';

export const ValueWithLabel = ({ label, children }) => (
  <>
    <Box variant="awsui-key-label">
      {label}
    </Box>
    <>{children}</>
  </>
);
