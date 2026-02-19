import type { MultiChannelRingBuffer } from "../../lib/ringBuffer";
import { CHANNEL_COLORS } from "../../lib/models/types";

export interface RendererConfig {
  channelCount: number;
  sensorNames: string[];
  enabledChannels: boolean[];
  resolution: number; // 0.01 - 5.0
  scrollMode: boolean;
  lineWidth: number;
  baseline: number[];
  useBaseline: boolean;
}

/**
 * Imperative Canvas 2D renderer for real-time EEG waveforms.
 * Uses double-buffering scroll technique from legacy graphics.js.
 */
export class EEGCanvasRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private buffer: HTMLCanvasElement;
  private btx: CanvasRenderingContext2D;
  private width = 0;
  private height = 0;
  private cx = 0; // current x position
  private oldx = 0;
  private oldy: number[] = [];
  private slowScroll = 0;
  private animId = 0;
  private running = false;
  private ringBufferRef: { current: MultiChannelRingBuffer } | null = null;
  private config: RendererConfig;
  /**
   * Track total samples consumed per channel using the ring buffer's
   * monotonic `totalPushed` counter — this never wraps, so we can always
   * know exactly how many new samples have arrived since the last frame.
   */
  private lastTotalPushed = 0;

  constructor(canvas: HTMLCanvasElement, config: RendererConfig) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d", { alpha: false })!;
    this.buffer = document.createElement("canvas");
    this.btx = this.buffer.getContext("2d", { alpha: false })!;
    this.config = config;
    this.oldy = new Array(config.channelCount).fill(0);

    this.ctx.imageSmoothingEnabled = false;
    this.btx.imageSmoothingEnabled = false;
  }

  setRingBuffer(ref: { current: MultiChannelRingBuffer }): void {
    this.ringBufferRef = ref;
    this.lastTotalPushed = 0;
  }

  updateConfig(config: Partial<RendererConfig>): void {
    Object.assign(this.config, config);
  }

  resize(): void {
    const rect = this.canvas.parentElement?.getBoundingClientRect();
    if (!rect) return;

    const dpr = window.devicePixelRatio || 1;
    this.width = Math.floor(rect.width);
    this.height = Math.floor(rect.height);

    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;

    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    this.buffer.width = this.width * dpr;
    this.buffer.height = this.height * dpr;
    this.btx.setTransform(dpr, 0, 0, dpr, 0, 0);

    this.cx = this.width - 3;
    this.oldx = this.cx - 1;

    // Clear and redraw background
    this.clearCanvas();
  }

  private clearCanvas(): void {
    this.ctx.fillStyle = "#111111";
    this.ctx.fillRect(0, 0, this.width, this.height);
    this.btx.fillStyle = "#111111";
    this.btx.fillRect(0, 0, this.width, this.height);

    this.drawGrid();
  }

  private drawGrid(): void {
    this.ctx.strokeStyle = "#1a1a1a";
    this.ctx.lineWidth = 0.5;

    const { channelCount, enabledChannels } = this.config;
    const activeCount = enabledChannels.filter(Boolean).length || channelCount;
    const step = this.height / (activeCount + 1);

    for (let i = 1; i <= activeCount; i++) {
      const y = step * i;
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.width, y);
      this.ctx.stroke();
    }
  }

  private drawDot(
    channelIdx: number,
    offset: number,
    x: number,
    y: number,
    color: string,
  ): void {
    const ctx = this.ctx;
    const rx = Math.round(x);
    const rox = Math.round(this.oldx);

    ctx.beginPath();
    ctx.lineWidth = this.config.lineWidth;
    ctx.strokeStyle = color;
    ctx.moveTo(rox + 1, y + offset);
    ctx.lineTo(rx, this.oldy[channelIdx] || y + offset);
    ctx.stroke();

    this.oldy[channelIdx] = y + offset;
  }

  private scrollScreen(): void {
    if (!this.config.scrollMode) return;

    this.slowScroll += 2;
    if (this.slowScroll > 2) {
      this.slowScroll = 0;
      this.btx.drawImage(this.canvas, 0, 0, this.width, this.height);
      this.ctx.fillStyle = "#111111";
      this.ctx.fillRect(0, 0, this.width, this.height);
      this.ctx.drawImage(this.buffer, -1, 0, this.width, this.height);
      this.btx.fillStyle = "#111111";
      this.btx.fillRect(0, 0, this.width, this.height);
    }
  }

  private moveForward(): void {
    this.scrollScreen();

    if (this.config.scrollMode) {
      this.cx = this.width - 5;
      this.oldx = this.cx;
    } else {
      this.cx += 1;
      this.oldx = this.cx;

      if (this.cx > this.width) {
        this.oldx = 0;
        this.cx = 0;
        this.clearCanvas();
      }
    }
  }

  private renderFrame = (): void => {
    if (!this.running || !this.ringBufferRef) {
      this.animId = requestAnimationFrame(this.renderFrame);
      return;
    }

    const rb = this.ringBufferRef.current;
    const { channelCount, enabledChannels, resolution, baseline, useBaseline } =
      this.config;

    // Use the monotonic totalPushed counter from channel 0 to detect new data.
    const ch0 = rb.getChannel(0);
    const currentTotal = ch0.totalPushed;
    const newSamples = currentTotal - this.lastTotalPushed;

    if (newSamples > 0) {
      // Process ALL new samples (up to a sane max to avoid freeze on huge bursts).
      // 128Hz / 60fps ≈ 2 samples/frame typically; allow up to 16 for burst recovery.
      const toProcess = Math.min(newSamples, 16);

      // Pre-compute which channels are active
      const activeChannels: number[] = [];
      for (let ch = 0; ch < channelCount; ch++) {
        if (enabledChannels[ch]) {
          activeChannels.push(ch);
        }
      }
      const step = this.height / (activeChannels.length + 1);

      for (let s = 0; s < toProcess; s++) {
        // How far back from the newest sample is this one?
        const fromEnd = toProcess - 1 - s;

        for (let i = 0; i < activeChannels.length; i++) {
          const ch = activeChannels[i];
          const channel = rb.getChannel(ch);
          const rawValue = channel.getFromEnd(fromEnd);
          const baselineVal = useBaseline ? (baseline[ch] || 0) : 0;
          const value = (baselineVal - rawValue) * resolution;
          const yOffset = step * (i + 1);
          const color = CHANNEL_COLORS[ch % CHANNEL_COLORS.length];

          this.drawDot(ch, yOffset, this.cx, value, color);
        }

        this.moveForward();
      }

      // Mark all samples as consumed (even if we skipped some due to the cap)
      this.lastTotalPushed = currentTotal;
    }

    this.animId = requestAnimationFrame(this.renderFrame);
  };

  start(): void {
    if (this.running) return;
    this.running = true;
    // Sync with current ring buffer state so we don't replay old data
    if (this.ringBufferRef) {
      this.lastTotalPushed = this.ringBufferRef.current.getChannel(0).totalPushed;
    }
    this.resize();
    this.animId = requestAnimationFrame(this.renderFrame);
  }

  stop(): void {
    this.running = false;
    if (this.animId) {
      cancelAnimationFrame(this.animId);
      this.animId = 0;
    }
  }

  destroy(): void {
    this.stop();
  }
}
