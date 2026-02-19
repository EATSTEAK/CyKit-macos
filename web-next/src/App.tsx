import { useState, useCallback, useMemo } from "react";
import { AppShell } from "./components/layout/AppShell";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { TabBar, type TabId } from "./components/layout/TabBar";
import { EEGCanvas } from "./components/eeg/EEGCanvas";
import { ChannelSelector } from "./components/eeg/ChannelSelector";
import { CalibrationPanel } from "./components/calibration/CalibrationPanel";
import { RecordingPanel } from "./components/recording/RecordingPanel";
import { useWebSocket, commands } from "./hooks/useWebSocket";
import { useDeviceInfo } from "./hooks/useDeviceInfo";
import { useEEGData } from "./hooks/useEEGData";
import { useRecording } from "./hooks/useRecording";
import { useBaseline } from "./hooks/useBaseline";
import { supportsFormatSwitch, computeBackendFormat } from "./lib/models/registry";
import type { CommandMessage, DataMessage } from "./lib/protocol";
import type { RendererConfig } from "./components/eeg/EEGCanvasRenderer";

const DEFAULT_SENSOR_NAMES = [
  "AF3", "F7", "F3", "FC5", "T7", "P7", "O1",
  "O2", "P8", "T8", "FC6", "F4", "F8", "AF4",
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("eeg");
  const [scrollMode, setScrollMode] = useState(false);
  const [boldLine, setBoldLine] = useState(false);
  const [resolution, setResolution] = useState(0.5);
  const [displayFormat, setDisplayFormat] = useState<"float" | "raw">("float");
  const [enabledChannels, setEnabledChannels] = useState<boolean[]>(
    () => new Array(14).fill(true),
  );

  // --- Device & data hooks ---
  const deviceInfo = useDeviceInfo();
  const eegData = useEEGData();

  const onCommand = useCallback(
    (msg: CommandMessage) => {
      deviceInfo.handleCommand(msg);
    },
    [deviceInfo],
  );

  const onData = useCallback(
    (msg: DataMessage) => {
      const battery = eegData.handleData(
        msg,
        deviceInfo.modelConfig.current,
        deviceInfo.parseOpts.current,
      );
      if (battery !== null && battery !== undefined) {
        deviceInfo.updateBattery(battery);
      }
    },
    [eegData, deviceInfo],
  );

  const ws = useWebSocket({
    onCommand,
    onData,
    onStatusChange: (status) => {
      if (status === "connected") {
        ws.sendCommand(commands.setDataMode(1));
        // Enable Python-side baseline immediately (DC offset removal)
        ws.sendCommand(commands.setBaselineMode(1));
      }
      if (status === "disconnected") {
        deviceInfo.reset();
        eegData.clear();
      }
    },
  });

  const recording = useRecording(ws.sendCommand);
  const baseline = useBaseline(ws.sendCommand);

  // --- Format switching ---
  const showFormatSelector = supportsFormatSwitch(deviceInfo.info.keyModel);

  const handleFormatChange = useCallback(
    (format: "float" | "raw") => {
      setDisplayFormat(format);
      const localFormat = format === "float" ? 0 : 1;
      deviceInfo.setFormatType(localFormat);

      const backendFormat = computeBackendFormat(
        deviceInfo.info.keyModel,
        deviceInfo.info.config.bluetooth,
        format,
      );
      ws.sendCommand(commands.changeFormat(backendFormat));
    },
    [deviceInfo, ws],
  );

  // --- Sensor names from detected model ---
  const sensorNames = useMemo(() => {
    const cfg = deviceInfo.modelConfig.current;
    return cfg?.sensorMap.names ?? DEFAULT_SENSOR_NAMES;
  }, [deviceInfo.info.keyModel]); // eslint-disable-line react-hooks/exhaustive-deps

  const channelCount = sensorNames.length;

  // Sync enabled channels when model changes
  const currentEnabledChannels = useMemo(() => {
    if (enabledChannels.length !== channelCount) {
      return new Array(channelCount).fill(true);
    }
    return enabledChannels;
  }, [enabledChannels, channelCount]);

  const handleChannelToggle = useCallback(
    (index: number, enabled: boolean) => {
      setEnabledChannels((prev) => {
        const next = [...prev];
        while (next.length < channelCount) next.push(true);
        next[index] = enabled;
        return next;
      });
    },
    [channelCount],
  );

  const handleToggleAll = useCallback(
    (enabled: boolean) => {
      setEnabledChannels(new Array(channelCount).fill(enabled));
    },
    [channelCount],
  );

  // --- Canvas renderer config ---
  const rendererConfig: RendererConfig = useMemo(
    () => ({
      channelCount,
      sensorNames,
      enabledChannels: currentEnabledChannels,
      resolution,
      scrollMode,
      lineWidth: boldLine ? 1.5 : 0.6,
      baseline: eegData.baseline.current,
      useBaseline: baseline.baselineEnabled,
    }),
    [
      channelCount,
      sensorNames,
      currentEnabledChannels,
      resolution,
      scrollMode,
      boldLine,
      baseline.baselineEnabled,
    ], // eslint-disable-line react-hooks/exhaustive-deps
  );

  // --- Tab content ---
  const renderTabContent = () => {
    switch (activeTab) {
      case "eeg":
        return (
          <div className="flex flex-col h-full">
            <div className="flex-1 min-h-0">
              <EEGCanvas
                ringBufferRef={eegData.ringBuffer}
                config={rendererConfig}
              />
            </div>
            <div className="p-2 border-t border-border bg-panel">
              <ChannelSelector
                sensorNames={sensorNames}
                enabledChannels={currentEnabledChannels}
                onChange={handleChannelToggle}
                onToggleAll={handleToggleAll}
              />
            </div>
          </div>
        );
      case "calibration":
        return (
          <div className="flex h-full">
            <div className="flex-1 min-h-0">
              <EEGCanvas
                ringBufferRef={eegData.ringBuffer}
                config={rendererConfig}
              />
            </div>
            <div className="w-56 border-l border-border bg-panel overflow-y-auto">
              <CalibrationPanel
                baselineEnabled={baseline.baselineEnabled}
                pyBaseline={baseline.pyBaseline}
                onToggleBaseline={baseline.toggleBaseline}
                onTogglePyBaseline={baseline.togglePyBaseline}
                onResetBaseline={baseline.resetBaseline}
                scrollMode={scrollMode}
                onScrollModeChange={setScrollMode}
                boldLine={boldLine}
                onBoldLineChange={setBoldLine}
              />
            </div>
          </div>
        );
      case "recording":
        return (
          <RecordingPanel
            isRecording={recording.isRecording}
            filename={recording.filename}
            onFilenameChange={recording.setFilename}
            onStart={recording.startRecording}
            onStop={recording.stopRecording}
          />
        );
    }
  };

  return (
    <AppShell
      header={
        <Header
          status={ws.status}
          onConnect={ws.connect}
          onDisconnect={ws.disconnect}
        />
      }
      sidebar={
        <Sidebar
          deviceInfo={deviceInfo.info}
          sensorNames={sensorNames}
          quality={eegData.quality.current}
          resolution={resolution}
          onResolutionChange={setResolution}
          scrollMode={scrollMode}
          onScrollModeChange={setScrollMode}
          showFormatSelector={showFormatSelector}
          displayFormat={displayFormat}
          onFormatChange={handleFormatChange}
        />
      }
      tabBar={<TabBar activeTab={activeTab} onChange={setActiveTab} />}
    >
      {renderTabContent()}
    </AppShell>
  );
}
