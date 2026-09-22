import React, { useRef, useEffect } from 'react';

interface OceanHeroCanvasProps {
  className?: string;
  particleCount?: number;
}

interface Particle {
  x: number;
  y: number;
  speed: number;
  life: number;
  maxLife: number;
  size: number;
  alpha: number;
}

export const OceanHeroCanvas: React.FC<OceanHeroCanvasProps> = ({
  className = '',
  particleCount = 65,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Streamline particles
    const particles: Particle[] = [];
    const initParticle = (p?: Partial<Particle>): Particle => ({
      x: p?.x ?? Math.random() * width,
      y: p?.y ?? Math.random() * height,
      speed: 0.4 + Math.random() * 0.8,
      life: p?.life ?? Math.random() * 200,
      maxLife: 150 + Math.random() * 200,
      size: 1 + Math.random() * 1.5,
      alpha: 0.1 + Math.random() * 0.35,
    });

    for (let i = 0; i < particleCount; i++) {
      particles.push(initParticle());
    }

    let time = 0;

    // Vector field calculation (Streamlines & gyres)
    const getFlowVector = (x: number, y: number, t: number) => {
      const scale = 0.003;
      const angle1 = Math.sin(x * scale + t * 0.0008) * Math.cos(y * scale + t * 0.0006) * Math.PI * 2;
      const angle2 = Math.cos((x + y) * scale * 0.5 - t * 0.0005) * Math.PI;
      const angle = angle1 * 0.6 + angle2 * 0.4;
      return {
        u: Math.cos(angle),
        v: Math.sin(angle),
      };
    };

    const renderContourLines = () => {
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.04)';
      ctx.lineWidth = 1;

      const spacing = 70;
      for (let y = 0; y < height; y += spacing) {
        ctx.beginPath();
        for (let x = 0; x < width; x += 15) {
          const vec = getFlowVector(x, y, time);
          const dy = vec.v * 18;
          if (x === 0) ctx.moveTo(x, y + dy);
          else ctx.lineTo(x, y + dy);
        }
        ctx.stroke();
      }
    };

    const render = () => {
      time += 1;
      ctx.fillStyle = 'rgba(3, 7, 18, 0.18)';
      ctx.fillRect(0, 0, width, height);

      // Render flowing bathymetric contour wave lines
      renderContourLines();

      // Update and render flow particles
      particles.forEach((p, idx) => {
        const vec = getFlowVector(p.x, p.y, time);
        p.x += vec.u * p.speed;
        p.y += vec.v * p.speed;
        p.life += 1;

        // Wrap boundaries
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        if (p.life > p.maxLife) {
          particles[idx] = initParticle({ life: 0 });
        }

        // Particle fade curve
        const lifeFactor = Math.sin((p.life / p.maxLife) * Math.PI);
        const currentAlpha = p.alpha * lifeFactor;

        // Glow particle
        ctx.fillStyle = `rgba(56, 189, 248, ${currentAlpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();

        // Subtle motion trail
        ctx.strokeStyle = `rgba(14, 165, 233, ${currentAlpha * 0.5})`;
        ctx.lineWidth = p.size * 0.8;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - vec.u * 8, p.y - vec.v * 8);
        ctx.stroke();
      });

      if (!prefersReducedMotion) {
        animationId = requestAnimationFrame(render);
      }
    };

    // Initial background clear
    ctx.fillStyle = '#030712';
    ctx.fillRect(0, 0, width, height);
    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [particleCount]);

  return (
    <canvas
      ref={canvasRef}
      className={`ocean-hero-canvas ${className}`}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
};
