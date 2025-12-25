import { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  mediaRef: React.RefObject<HTMLMediaElement>;
  mode: 'bars' | 'wave' | 'oscilloscope';
  className?: string;
}

const AudioVisualizer = ({ mediaRef, mode, className }: AudioVisualizerProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode>();
  const sourceRef = useRef<MediaElementAudioSourceNode>();
  const audioContextRef = useRef<AudioContext>();

  useEffect(() => {
    // Initialize Audio Context and Analyser
    if (!mediaRef.current) return;

    const initAudio = () => {
      if (!audioContextRef.current) {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        audioContextRef.current = new AudioContext();
      }

      const ctx = audioContextRef.current;

      // Resume context if suspended (browser autoplay policy)
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      if (!analyserRef.current) {
        analyserRef.current = ctx.createAnalyser();
        analyserRef.current.fftSize = 2048; // Higher resolution for better visuals
      }

      if (!sourceRef.current) {
        // Connect media element to analyser and destination
        try {
            sourceRef.current = ctx.createMediaElementSource(mediaRef.current!);
            sourceRef.current.connect(analyserRef.current);
            analyserRef.current.connect(ctx.destination);
        } catch (e) {
            console.error("Error creating MediaElementSource:", e);
        }
      }
    };

    // Initialize on mount or when media changes.
    // Note: createMediaElementSource can only be called once per element.
    // We assume mediaRef.current is stable.
    initAudio();

    // Handle user interaction to resume context if needed
    const handlePlay = () => {
       if (audioContextRef.current?.state === 'suspended') {
           audioContextRef.current.resume();
       }
    };

    mediaRef.current.addEventListener('play', handlePlay);

    return () => {
       mediaRef.current?.removeEventListener('play', handlePlay);
       // We don't close the context immediately to avoid issues if component remounts quickly,
       // but typically you might want to cleanup.
       // For a single page app with persistent player, keeping context is usually fine.
    };
  }, [mediaRef]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Get theme colors from CSS variables
    const computedStyle = getComputedStyle(canvas);
    // Helper to get color from HSL var
    const getColor = (variable: string, fallback: string) => {
        const value = computedStyle.getPropertyValue(variable).trim();
        // Simple heuristic: if it contains 'hsl', use it, otherwise use fallback
        return value ? `hsl(${value})` : fallback;
    };

    const primaryColor = getColor('--primary', '#00f0ff');
    const secondaryColor = getColor('--secondary', '#7000ff');

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      if (mode === 'bars') {
        analyser.getByteFrequencyData(dataArray);

        const barWidth = (width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;

        // Gradient for bars
        const gradient = ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, secondaryColor);
        gradient.addColorStop(1, primaryColor);
        ctx.fillStyle = gradient;

        // Draw fewer bars for cleaner look
        const steps = 64;
        const stepSize = Math.floor(bufferLength / steps);

        for (let i = 0; i < steps; i++) {
           // Average out the frequency for this step
           let sum = 0;
           for(let j=0; j<stepSize; j++) {
               sum += dataArray[(i * stepSize) + j];
           }
           const average = sum / stepSize;

           barHeight = (average / 255) * height;

           ctx.fillRect(x, height - barHeight, (width / steps) - 2, barHeight);
           x += (width / steps);
        }

      } else if (mode === 'wave') {
        analyser.getByteTimeDomainData(dataArray);

        ctx.lineWidth = 2;
        ctx.strokeStyle = primaryColor;
        ctx.beginPath();

        const sliceWidth = width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * height) / 2;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
          x += sliceWidth;
        }

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();

      } else if (mode === 'oscilloscope') {
        // Circular Oscilloscope / Lissajous-ish style
        analyser.getByteTimeDomainData(dataArray);

        ctx.lineWidth = 2;
        ctx.strokeStyle = secondaryColor;
        ctx.beginPath();

        const cx = width / 2;
        const cy = height / 2;
        const radius = Math.min(width, height) / 3;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0; // 0..2
            const angle = (i / bufferLength) * Math.PI * 2;

            // Add some noise/distortion based on audio data
            const r = radius * v;

            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);

            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }

        ctx.closePath();
        ctx.stroke();

        // Add a glow effect
        ctx.shadowBlur = 10;
        ctx.shadowColor = primaryColor;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      animationRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [mode]);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      width={600}
      height={200}
    />
  );
};

export default AudioVisualizer;
