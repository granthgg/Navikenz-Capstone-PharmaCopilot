import React from 'react';

const LoadingSpinner = ({ 
  size = 'medium', 
  color = '#000000', 
  message = null,
  className = '',
  fullScreen = false,
  minimal = false 
}) => {
  const sizeMap = {
    small: 16,
    medium: 24,
    large: 32,
    xlarge: 48
  };

  const spinnerSize = sizeMap[size] || sizeMap.medium;

  const SpinnerComponent = () => (
    <div className={`loading-spinner ${className}`} style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      gap: minimal ? '0' : '0.75rem'
    }}>
      <div
        style={{
          width: spinnerSize,
          height: spinnerSize,
          border: `2px solid #e0e0e0`,
          borderTop: `2px solid ${color}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}
      />
      {message && !minimal && (
        <div style={{
          fontSize: size === 'small' ? '0.75rem' : size === 'large' ? '0.9rem' : '0.8rem',
          color: color,
          fontWeight: '500',
          textAlign: 'center',
          maxWidth: '200px',
          lineHeight: '1.4'
        }}>
          {message}
        </div>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999
      }}>
        <SpinnerComponent />
      </div>
    );
  }

  return <SpinnerComponent />;
};

// Simple three dot loading animation
export const DotsLoader = ({ color = '#000000', size = 6 }) => (
  <div style={{ display: 'flex', gap: `${size / 2}px`, alignItems: 'center' }}>
    {[0, 1, 2].map((index) => (
      <div
        key={index}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          backgroundColor: color,
          animation: `dots-loading 1.4s ease-in-out infinite`,
          animationDelay: `${index * 0.16}s`
        }}
      />
    ))}
  </div>
);

// Simple progress bar component
export const ProgressBar = ({ 
  progress = 0, 
  color = '#000000', 
  backgroundColor = '#e9ecef',
  height = 4,
  animated = false,
  className = ''
}) => (
  <div 
    className={className}
    style={{
      width: '100%',
      height: height,
      backgroundColor: backgroundColor,
      borderRadius: height / 2,
      overflow: 'hidden'
    }}
  >
    <div
      style={{
        height: '100%',
        width: animated ? '100%' : `${Math.min(100, Math.max(0, progress))}%`,
        backgroundColor: color,
        borderRadius: height / 2,
        transition: animated ? 'none' : 'width 0.3s ease',
        animation: animated ? 'progress-indeterminate 2s ease-in-out infinite' : 'none'
      }}
    />
  </div>
);

export default LoadingSpinner;
