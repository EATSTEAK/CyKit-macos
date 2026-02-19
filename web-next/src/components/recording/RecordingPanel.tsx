interface Props {
  isRecording: boolean;
  filename: string;
  onFilenameChange: (name: string) => void;
  onStart: () => void;
  onStop: () => void;
}

export function RecordingPanel({
  isRecording,
  filename,
  onFilenameChange,
  onStart,
  onStop,
}: Props) {
  return (
    <div className="space-y-4 p-4">
      <div>
        <div className="text-text-dim text-[10px] tracking-widest mb-1">RECORDING</div>
        <div className="border-t border-border mb-4" />

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <label className="text-text-dim text-[11px] w-16">Filename</label>
            <input
              type="text"
              value={filename}
              onChange={(e) => onFilenameChange(e.target.value)}
              disabled={isRecording}
              className="flex-1"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={onStart}
              disabled={isRecording}
              className={`flex-1 ${
                isRecording
                  ? "opacity-50 cursor-not-allowed"
                  : "border-accent text-accent hover:bg-accent hover:text-bg"
              }`}
            >
              {isRecording ? "Recording..." : "Record"}
            </button>
            <button
              onClick={onStop}
              disabled={!isRecording}
              className={`flex-1 ${
                !isRecording
                  ? "opacity-50 cursor-not-allowed"
                  : "border-red text-red hover:bg-red hover:text-bg"
              }`}
            >
              Stop
            </button>
          </div>

          {isRecording && (
            <div className="flex items-center gap-2 text-[10px]">
              <div className="w-2 h-2 bg-red animate-pulse" />
              <span className="text-red">REC</span>
              <span className="text-text-dim">{filename}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
