"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "../../../lib/api";

export default function VideoPage({ params }: { params: { scriptId: string } }) {
  const router = useRouter();
  const scriptId = params.scriptId;

  const [scenes, setScenes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [niche, setNiche] = useState("Social media ads");
  const [languageVoice, setLanguageVoice] = useState("English - Female");
  const [artStyle, setArtStyle] = useState("Comic");
  const [captionStyle, setCaptionStyle] = useState("Modern captions");
  const [effects, setEffects] = useState("None");
  const [socialAccounts, setSocialAccounts] = useState("");

  // Load scenes for this script
  const loadScenes = async () => {
    const res = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);
    const data = await res.json();
    setScenes(data.scenes);
    // Apply saved automation settings if present
    if (data.script?.settings) {
      const s = data.script.settings;
      setNiche(s.niche || niche);
      setLanguageVoice(s.language_voice || languageVoice);
      setArtStyle(s.art_style || artStyle);
      setCaptionStyle(s.caption_style || captionStyle);
      setEffects(s.effects || effects);
      setSocialAccounts(s.social_accounts || socialAccounts);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadScenes();
  }, []);

  const generateVideo = async (sceneId: string) => {
    await fetch(`${API_BASE_URL}/scenes/${sceneId}/generate-video`, {
      method: "POST",
    });

    pollForVideo(sceneId);
  };

  const pollForVideo = async (sceneId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`${API_BASE_URL}/scenes/${sceneId}`);
      const scene = await res.json();

      if (scene.video_url) {
        loadScenes();
        clearInterval(interval);
      }
    }, 3000);
  };

  if (loading) return <div className="p-6">Loading video generator...</div>;

  return (
    <div className="max-w-4xl mx-auto py-10 px-6">
      <h1 className="text-3xl font-bold mb-6">Generate Video Clips</h1>

      <p className="text-gray-600 mb-8">
        Each scene will be turned into an AI‑generated video clip using your selected style, image, and voice.
      </p>

      <div className="border rounded p-4 bg-gray-50 mb-6">
        <h3 className="font-semibold mb-2">Automation Settings</h3>
        <div className="grid md:grid-cols-2 gap-3">
          <select value={niche} onChange={(e) => setNiche(e.target.value)} className="border rounded px-2 py-1">
            <option>Social media ads</option>
            <option>Personal branding</option>
            <option>Product launch</option>
            <option>Education & tutorials</option>
          </select>
          <select value={languageVoice} onChange={(e) => setLanguageVoice(e.target.value)} className="border rounded px-2 py-1">
            <option>English - Female</option>
            <option>English - Male</option>
            <option>Spanish - Female</option>
          </select>
          <select value={artStyle} onChange={(e) => setArtStyle(e.target.value)} className="border rounded px-2 py-1">
            <option>Comic</option>
            <option>Anime</option>
            <option>Cinematic</option>
          </select>
          <select value={effects} onChange={(e) => setEffects(e.target.value)} className="border rounded px-2 py-1">
            <option>None</option>
            <option>Glitch</option>
            <option>VHS</option>
          </select>
          <input value={socialAccounts} onChange={(e) => setSocialAccounts(e.target.value)} placeholder="Social handles" className="border rounded px-2 py-1" />
        </div>
      </div>

      <div className="space-y-6">
        {scenes.map((scene) => (
          <div
            key={scene.id}
            className="border rounded-lg p-4 shadow-sm bg-white"
          >
            <h2 className="text-xl font-semibold mb-2">
              Scene {scene.index + 1}
            </h2>

            {/* Scene Description */}
            <p className="text-gray-700 mb-3">{scene.description}</p>

            {/* Image Preview */}
            {scene.image_url ? (
              <img
                src={scene.image_url}
                alt="Scene Image"
                className="w-full rounded mb-3"
              />
            ) : (
              <div className="text-gray-500 italic mb-3">
                No image generated yet
              </div>
            )}

            {/* Voice Preview */}
            {scene.voice_audio_url ? (
              <audio controls src={scene.voice_audio_url} className="w-full mb-3" />
            ) : (
              <div className="text-gray-500 italic mb-3">
                No voice generated yet
              </div>
            )}

            {/* Video Preview */}
            {scene.video_url ? (
              <video
                controls
                src={scene.video_url}
                className="w-full rounded mb-3"
              />
            ) : (
              <div className="text-gray-500 italic mb-3">
                No video generated yet
              </div>
            )}

            {/* Generate Video Button */}
            <button
              onClick={() => generateVideo(scene.id)}
              className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
              Generate Video Clip
            </button>
          </div>
        ))}
      </div>

      {/* Continue Button */}
      <div className="mt-10">
        <button
          onClick={() => router.push(`/render/${scriptId}`)}
          className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700"
        >
          Continue to Final Render
        </button>
      </div>
    </div>
  );
}
