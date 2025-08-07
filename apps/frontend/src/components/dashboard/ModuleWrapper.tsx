import { Component, ErrorInfo, ReactNode } from 'react';
import { DashboardModule } from '@/types/dashboard';

interface Props {
  module: DashboardModule;
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ModuleWrapper extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(): State {
    return { hasError: true };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`Module ${this.props.module.id} error:`, error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div 
          className={`dashboard-module module-${this.props.module.id}`}
          data-module-id={this.props.module.id}
          style={{
            background: '#262626',
            border: '1px solid #404040',
            borderRadius: '0.5rem',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <div className="module-header" style={{
            padding: '1rem 1.5rem',
            borderBottom: '1px solid #404040',
            background: '#404040'
          }}>
            <h3 style={{margin: 0, fontSize: '1.125rem', color: 'white'}}>
              {this.props.module.title}
            </h3>
          </div>
          <div className="module-content" style={{padding: '1.5rem', flex: 1}}>
            <div className="module-error" style={{padding: '2rem', textAlign: 'center'}}>
              <p style={{color: '#666'}}>Unable to load this module</p>
              <button 
                onClick={() => this.setState({ hasError: false })}
                className="retry-btn"
                style={{
                  marginTop: '1rem',
                  padding: '0.5rem 1rem',
                  border: '1px solid #666',
                  background: 'transparent',
                  color: '#666',
                  borderRadius: '0.25rem',
                  cursor: 'pointer'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = '#666';
                  e.currentTarget.style.color = 'white';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#666';
                }}
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div 
        className={`dashboard-module module-${this.props.module.id}`}
        data-module-id={this.props.module.id}
        style={{
          background: '#262626',
          border: '1px solid #404040',
          borderRadius: '0.5rem',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <div className="module-header" style={{
          padding: '1rem 1.5rem',
          borderBottom: '1px solid #404040',
          background: '#404040'
        }}>
          <h3 style={{margin: 0, fontSize: '1.125rem', color: 'white'}}>
            {this.props.module.title}
          </h3>
        </div>
        <div className="module-content" style={{padding: '1.5rem', flex: 1, overflowY: 'auto'}}>
          {this.props.children}
        </div>
      </div>
    );
  }
}