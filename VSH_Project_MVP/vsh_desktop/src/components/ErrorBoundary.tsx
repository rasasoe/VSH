import React, { ReactNode, ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 20, backgroundColor: '#ffebee', borderRadius: 8, border: '1px solid #ef5350', marginTop: 20 }}>
          <h2 style={{ color: '#c62828', marginTop: 0 }}>⚠️ 렌더링 오류 발생</h2>
          <p style={{ color: '#d32f2f', marginBottom: 10 }}>UI에서 오류가 발생했습니다.</p>
          <pre style={{ 
            backgroundColor: '#fff', 
            padding: 10, 
            borderRadius: 4, 
            overflow: 'auto',
            fontSize: '12px',
            color: '#666',
            border: '1px solid #ddd'
          }}>
            {this.state.error?.message}
          </pre>
          <button 
            onClick={() => window.location.reload()}
            style={{
              marginTop: 10,
              padding: '8px 16px',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer'
            }}
          >
            🔄 새로고침
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
