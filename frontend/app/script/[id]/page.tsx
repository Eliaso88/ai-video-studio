"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "../../../lib/api";

export default function SceneEditorPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const scriptId = params.id;

  const [script, setScript] = useState<any>(null);
  const [scenes, setScenes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [niche, setNiche] = useState("Social media ads");
  const [languageVoice, setLanguageVoice] = useState("English - Female");
  const [artStyle, setArtStyle] = useState("Comic");
  const [captionStyle, setCaptionStyle] = useState("Modern captions");
  const [effects, setEffects] = useState("None");
  const [socialAccounts, setSocialAccounts] = useState("");

  // Fetch script + scenes
  const loadScript = async () => {
    const res = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);
    const data = await res.json();
    setScript(data.script);
    setScenes(data.scenes);
    setLoading(false);
  };

  // load saved automation settings if present
  useEffect(() => {
    if (script && script.settings) {
      const s = script.settings;
      setNiche(s.niche || niche);
      setLanguageVoice(s.language_voice || languageVoice);
      setArtStyle(s.art_style || artStyle);
      setCaptionStyle(s.caption_style || captionStyle);
      setEffects(s.effects || effects);
      setSocialAccounts(s.social_accounts || socialAccounts);
    }
  }, [script]);

  useEffect(() => {
    loadScript();
  }, []);

  const updateScene = async (sceneId: string, updates: any) => {
    await fetch(`${API_BASE_URL}/scenes/${sceneId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    loadScript();
  };

  const generateImage = async (sceneId: string) => {
    await fetch(`${API_BASE_URL}/scenes/${sceneId}/generate-image`, {
      method: "POST",
    });

    pollForImage(sceneId);
  };

  const saveAutomation = async () => {
    const payload = {
      settings: {
        niche,
        language_voice: languageVoice,
        art_style: artStyle,
        caption_style: captionStyle,
        effects,
        social_accounts: socialAccounts,
      },
    };
    await fetch(`${API_BASE_URL}/scripts/${scriptId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    loadScript();
  };

  const pollForImage = async (sceneId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`${API_BASE_URL}/scenes/${sceneId}`);
      const scene = await res.json();

      if (scene.image_url) {
        loadScript();
        clearInterval(interval);
      }
    }, 2000);
  };

  if (loading) return <div className="p-6">Loading scenes...</div>;

  return (
    <div className="max-w-4xl mx-auto py-10 px-6">
      <h1 className="text-3xl font-bold mb-6">{script.title}</h1>

      <div className="space-y-6">
        {/* Automation quick settings (local) */}
        <div className="border rounded p-4 bg-gray-50 mb-6">
          <h3 className="font-semibold mb-2">Automation Settings</h3>
          <div className="grid md:grid-cols-2 gap-3">
            <select value={niche} onChange={(e) => setNiche(e.target.value)} className="border rounded px-2 py-1">
              <option>Social media ads</option>
              <option>Personal branding</option>
              <option>Product launch</option>
              <option>Education & tutorials</option>
              <option>Entertainment</option>
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
              <option>Minimal</option>
            </select>
            <select value={effects} onChange={(e) => setEffects(e.target.value)} className="border rounded px-2 py-1">
              <option>None</option>
              <option>Glitch</option>
              <option>VHS</option>
            </select>
            <input value={socialAccounts} onChange={(e) => setSocialAccounts(e.target.value)} placeholder="Social handles" className="border rounded px-2 py-1" />
            <div />
          </div>
        </div>
        {scenes.map((scene) => (
          <div
            key={scene.id}
            className="border rounded-lg p-4 shadow-sm bg-white"
          >
            <div className="flex justify-between items-center mb-3">
              <h2 classname="text-xl font-semibold">Scene {scene.index + 1}</h2>
            </div>

            {/* Title */}
            <label className="block font-medium">Title</label>
            <input
              className="w-full border rounded px-3 py-2 mb-3"
              value={scene.title}
              onChange={(e) =>
                updateScene(scene.id, { title: e.target.value })
              }
            />

            {/* Description */}
            <label className="block font-medium">Description</label>
            <textarea
              className="w-full border rounded px-3 py-2 mb-3"
              value={scene.description}
              onChange={(e) =>
                updateScene(scene.id, { description: e.target.value })
              }
            />

            {/* Duration */}
            <label className="block font-medium">Duration (seconds)</label>
            <input
              type="number"
              className="w-full border rounded px-3 py-2 mb-3"
              value={scene.duration_seconds}
              onChange={(e) =>
                updateScene(scene.id, {
                  duration_seconds: Number(e.target.value),
                })
              }
            />

            {/* Style */}
            <label className="block font-medium">Style</label>
            <select
              className="w-full border rounded px-3 py-2 mb-3"
              value={scene.style}
              onChange={(e) =>
                updateScene(scene.id, { style: e.target.value })
              }
            >
              <option value="cinematic">Cinematic</option>
              <option value="faceless_broll">Faceless B‑roll</option>
              <option value="avatar">Talking‑Head Avatar</option>
              <option value="animated">Animated / Stylized</option>
            </select>

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

            {/* Generate Image Button */}
            <button
              onClick={() => generateImage(scene.id)}
              className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
              Generate Image
            </button>
          </div>
        ))}
      </div>

      <div className="mt-10">
        <div className="flex gap-3">
          <button
            onClick={saveAutomation}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Save Automation Settings
          </button>
          <button
            onClick={() => router.push(`/voice/${scriptId}`)}
            className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700"
          >
            Continue to Voice & Video
          </button>
        </div>
      </div>
    </div>
  );
}
