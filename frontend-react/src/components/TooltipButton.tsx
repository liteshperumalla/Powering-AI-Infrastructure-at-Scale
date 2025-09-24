'use client';

import React from 'react';
import { Button, Tooltip, ButtonProps } from '@mui/material';

interface TooltipButtonProps extends ButtonProps {
  tooltip?: string;
  children: React.ReactNode;
}

const TooltipButton: React.FC<TooltipButtonProps> = ({
  tooltip,
  disabled,
  children,
  ...buttonProps
}) => {
  const button = (
    <Button disabled={disabled} {...buttonProps}>
      {children}
    </Button>
  );

  if (!tooltip) {
    return button;
  }

  // When button is disabled, wrap in span to allow tooltip to work
  if (disabled) {
    return (
      <Tooltip title={tooltip}>
        <span style={{ cursor: 'not-allowed' }}>
          {button}
        </span>
      </Tooltip>
    );
  }

  // When enabled, tooltip can wrap button directly
  return (
    <Tooltip title={tooltip}>
      {button}
    </Tooltip>
  );
};

export default TooltipButton;