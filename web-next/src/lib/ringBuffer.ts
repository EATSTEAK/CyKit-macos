/**
 * Float64Array-based circular buffer for EEG data.
 * O(1) insert, zero GC pressure, fixed memory footprint.
 */
export class RingBuffer {
  private buffer: Float64Array;
  private head = 0; // next write position
  private count = 0; // number of valid samples
  readonly capacity: number;
  /** Monotonically increasing counter — total number of pushes ever made. */
  totalPushed = 0;

  constructor(capacity: number) {
    this.capacity = capacity;
    this.buffer = new Float64Array(capacity);
  }

  push(value: number): void {
    this.buffer[this.head] = value;
    this.head = (this.head + 1) % this.capacity;
    if (this.count < this.capacity) {
      this.count++;
    }
    this.totalPushed++;
  }

  /** Number of valid samples stored */
  get length(): number {
    return this.count;
  }

  /**
   * Get sample at logical index (0 = oldest).
   * Returns 0 if index is out of range.
   */
  get(index: number): number {
    if (index < 0 || index >= this.count) return 0;
    const start = (this.head - this.count + this.capacity) % this.capacity;
    return this.buffer[(start + index) % this.capacity];
  }

  /** Get the most recently pushed value */
  latest(): number {
    if (this.count === 0) return 0;
    return this.buffer[(this.head - 1 + this.capacity) % this.capacity];
  }

  /**
   * Get the N-th most recent value (0 = latest, 1 = one before latest, ...).
   */
  getFromEnd(n: number): number {
    if (n < 0 || n >= this.count) return 0;
    return this.buffer[(this.head - 1 - n + this.capacity * 2) % this.capacity];
  }

  /** Clear all data */
  clear(): void {
    this.head = 0;
    this.count = 0;
    this.totalPushed = 0;
    this.buffer.fill(0);
  }

  /**
   * Read the last `n` samples into a plain array (newest last).
   * Useful for rendering a window of recent data.
   */
  readLast(n: number): Float64Array {
    const len = Math.min(n, this.count);
    const result = new Float64Array(len);
    const start = (this.head - len + this.capacity) % this.capacity;
    for (let i = 0; i < len; i++) {
      result[i] = this.buffer[(start + i) % this.capacity];
    }
    return result;
  }
}

/**
 * Multi-channel ring buffer manager.
 * Each channel has its own independent RingBuffer.
 */
export class MultiChannelRingBuffer {
  readonly channels: RingBuffer[];
  readonly channelCount: number;
  readonly samplesPerChannel: number;

  constructor(channelCount: number, samplesPerChannel: number) {
    this.channelCount = channelCount;
    this.samplesPerChannel = samplesPerChannel;
    this.channels = Array.from(
      { length: channelCount },
      () => new RingBuffer(samplesPerChannel),
    );
  }

  pushSample(channelIndex: number, value: number): void {
    if (channelIndex >= 0 && channelIndex < this.channelCount) {
      this.channels[channelIndex].push(value);
    }
  }

  getChannel(index: number): RingBuffer {
    return this.channels[index];
  }

  clear(): void {
    for (const ch of this.channels) {
      ch.clear();
    }
  }
}
