// Converts mic audio (float32) to 16-bit PCM and posts it in ~256 ms blocks.
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Int16Array(4096);
    this.offset = 0;
  }

  process(inputs) {
    const channel = inputs[0][0];
    if (!channel) return true;
    for (let i = 0; i < channel.length; i++) {
      const s = Math.max(-1, Math.min(1, channel[i]));
      this.buffer[this.offset++] = s < 0 ? s * 0x8000 : s * 0x7fff;
      if (this.offset === this.buffer.length) {
        this.port.postMessage(this.buffer.buffer.slice(0));
        this.offset = 0;
      }
    }
    return true;
  }
}

registerProcessor("pcm-processor", PCMProcessor);
