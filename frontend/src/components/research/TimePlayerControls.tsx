import React from 'react';
import { 
  Play, 
  Pause, 
  ChevronLeft, 
  ChevronRight, 
  Clock 
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';

export const TimePlayerControls: React.FC = () => {
  const {
    timeIndex,
    setTimeIndex,
    metadata,
    isPlaying,
    togglePlay,
    stepForward,
    stepBackward,
  } = useAnalysis();

  const totalSteps = metadata?.temporal_coverage?.time_steps_count || 
                     metadata?.temporal_extent?.total_timesteps || 1;

  if (totalSteps <= 1) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.625rem',
      padding: '0.375rem 0.75rem',
      backgroundColor: 'var(--bg-deep)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-sm)',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.75rem',
    }}>
      {/* Play/Pause Button */}
      <button
        onClick={togglePlay}
        title={isPlaying ? 'Pause timeline animation' : 'Play timeline animation'}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '26px',
          height: '26px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: isPlaying ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.2)',
          border: isPlaying ? '1px solid var(--accent-rose)' : '1px solid var(--border-focus)',
          color: isPlaying ? 'var(--accent-rose)' : 'var(--accent-cyan)',
          cursor: 'pointer',
        }}
      >
        {isPlaying ? <Pause size={13} /> : <Play size={13} style={{ marginLeft: '1px' }} />}
      </button>

      {/* Step Buttons */}
      <div style={{ display: 'flex', gap: '0.125rem' }}>
        <button
          onClick={stepBackward}
          title="Previous time step"
          style={{
            padding: '0.2rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '2px',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
          }}
        >
          <ChevronLeft size={14} />
        </button>
        <button
          onClick={stepForward}
          title="Next time step"
          style={{
            padding: '0.2rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '2px',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
          }}
        >
          <ChevronRight size={14} />
        </button>
      </div>

      {/* Time Step Indicator */}
      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--accent-cyan)', minWidth: '90px' }}>
        <Clock size={12} />
        <span>{timeIndex + 1} / {totalSteps}</span>
      </span>

      {/* Scrub Slider */}
      <input
        type="range"
        min={0}
        max={totalSteps - 1}
        value={timeIndex}
        onChange={(e) => setTimeIndex(parseInt(e.target.value))}
        style={{ width: '120px', accentColor: 'var(--accent-cyan)', cursor: 'pointer' }}
      />
    </div>
  );
};
