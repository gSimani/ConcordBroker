import React, { Component, ErrorInfo, ReactNode } from 'react';
import { generateElementId } from '@/utils/generateElementId';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          id={generateElementId('error-boundary', 'main', 'error-container', 1)}
          data-testid="error-boundary-container"
          style={{ padding: '20px', background: '#fee', border: '1px solid #fcc', borderRadius: '4px', margin: '20px' }}
        >
          <h2 style={{ color: '#c00' }}>Application Error</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            <summary>Click for details</summary>
            <p>{this.state.error && this.state.error.toString()}</p>
            <p>{this.state.errorInfo && this.state.errorInfo.componentStack}</p>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;