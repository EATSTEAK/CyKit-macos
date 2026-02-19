import { useEffect, useRef } from "react";
import { EEGCanvasRenderer, type RendererConfig } from "./EEGCanvasRenderer";
import type { MultiChannelRingBuffer } from "../../lib/ringBuffer";

interface Props {
  ringBufferRef: React.RefObject<MultiChannelRingBuffer>;
  config: RendererConfig;
}

export function EEGCanvas({ ringBufferRef, config }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<EEGCanvasRenderer | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const renderer = new EEGCanvasRenderer(canvas, config);
    renderer.setRingBuffer(ringBufferRef);
    rendererRef.current = renderer;

    renderer.start();

    const ro = new ResizeObserver(() => {
      renderer.resize();
    });
    ro.observe(canvas.parentElement!);

    return () => {
      ro.disconnect();
      renderer.destroy();
      rendererRef.current = null;
    };
    // Only re-create renderer when channel count changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.channelCount]);

  // Update config without re-creating the renderer
  useEffect(() => {
    rendererRef.current?.updateConfig(config);
  }, [config]);

  return (
    <div className="relative w-full h-full bg-panel border border-border overflow-hidden">
      <canvas
        ref={canvasRef}
        className="block w-full h-full"
      />
      {/* Channel labels overlay */}
      <div className="absolute left-1 top-0 bottom-0 flex flex-col justify-around pointer-events-none py-4">
        {config.sensorNames.map((name, i) =>
          config.enabledChannels[i] ? (
            <span
              key={name}
              className="text-[9px] leading-none px-1"
              style={{ color: `color-mix(in srgb, ${getChannelColor(i)} 70%, white)` }}
            >
              {name}
            </span>
          ) : null,
        )}
      </div>
    </div>
  );
}

function getChannelColor(index: number): string {
  const colors = [
    "#ff7f7f", "#ffbe7f", "#ffdf7f", "#dfff7f", "#a0ff7f", "#7fffdf", "#7fdfff",
    "#7fa0ff", "#a07fff", "#df7fff", "#ff7fdf", "#ff7fa0", "#ff7f7f", "#fdff7f",
  ];
  return colors[index % colors.length];
}
