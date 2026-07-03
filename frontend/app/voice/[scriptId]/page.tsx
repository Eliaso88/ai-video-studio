"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "../../../lib/api";

export default function VoicePage({ params }: { params: { scriptId: string } }) {
  const router = useRouter();
  const scriptId = params.scriptId;

  const [scenes, setScenes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [voice, setVoice] = useState("en-US-JennyNeural");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0);

  // Load scenes for this script
  const loadScenes = async () => {
    const res = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);
    const data = await res.json();
    setScenes(data.scenes);
    setLoading(false);
  };

  useEffect(() => {
    loadScenes();
  }, []);

  const generateVoice = async (sceneId: string) => {
    await fetch(`${API_BASE_URL}/scenes/${sceneId}/generate-voice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voice, speed, pitch }),
    });

    pollForVoice(sceneId);
  };

  const pollForVoice = async (sceneId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`${API_BASE_URL}/scenes/${sceneId}`);
      const scene = await res.json();

      if (scene.voice_audio_url) {
        loadScenes();
        clearInterval(interval);
      }
    }, 2000);
  };

  if (loading) return <div className="p-6">Loading voice settings...</div>;

  return (
    <div className="max-w-4xl mx-auto py-10 px-6">
      <h1 className="text-3xl font-bold mb-6">Voice Settings</h1>

      {/* Global Voice Controls */}
      <div className="border rounded-lg p-4 mb-8 bg-white shadow-sm">
        <h2 className="text-xl font-semibold mb-4">Global Voice Options</h2>

        {/* Voice Dropdown */}
        <label className="block font-medium">Voice</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={voice}
          onChange={(e) => setVoice(e.target.value)}
        >
          <option value="en-US-JennyNeural">Jenny (US Female)</option>
          <option value="en-US-GuyNeural">Guy (US Male)</option>
          <option value="en-GB-LibbyNeural">Libby (UK Female)</option>
          <option value="en-GB-RyanNeural">Ryan (UK Male)</option>
        </select>

        {/* Speed */}
        <label className="block font-medium">Speed ({speed}x)</label>
        <input
          type="range"
          min="0.5"
          max="1.5"
          step="0.1"
          value={speed}
          onChange={(e) => setSpeed(parseFloat(e.target.value))}
          className="w-full mb-4"
        />

        {/* Pitch */}
        <label className="block font-medium">Pitch ({pitch} Hz)</label>
        <input
          type="range"
          min="-10"
          max="10"
          step="1"
          value={pitch}
          onChange={(e) => setPitch(parseInt(e.target.value))}
          className="w-full mb-4"
        />
      </div>

      {/* Scene Voice Generation */}
      <div className="space-y-6">
        {scenes.map((scene) => (
          <div
            key={scene.id}
            className="border rounded-lg p-4 shadow-sm bg-white"
          >
            <h2 className="text-xl font-semibold mb-2">
              Scene {scene.index + 1}
            </h2>

            <p className="text-gray-700 mb-3">{scene.description}</p>

            {/* Audio Preview */}
            {scene.voice_audio_url ? (
              <audio controls src={scene.voice_audio_url} className="w-full mb-3" />
            ) : (
              <div className="text-gray-500 italic mb-3">
                No voice generated yet
              </div>
            )}

            {/* Generate Voice Button */}
            <button
              onClick={() => generateVoice(scene.id)}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              Generate Voice
            </button>
          </div>
        ))}
      </div>

      {/* Continue Button */}
      <div className="mt-10">
        <button
          onClick={() => router.push(`/video/${scriptId}`)}
          className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700"
        >
          Continue to Video Generation
        </button>
      </div>
    </div>
  );
}
