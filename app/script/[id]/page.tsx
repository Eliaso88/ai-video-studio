"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function SceneEditorPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const scriptId = params.id;

  const [script, setScript] = useState<any>(null);
  const [scenes, setScenes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch script + scenes
  const loadScript = async () => {
    const res = await fetch(`http://localhost:8000/scripts/${scriptId}`);
    const data = await res.json();
    setScript(data.script);
    setScenes(data.scenes);
    setLoading(false);
  };

  useEffect(() => {
    loadScript();
  }, []);

  const updateScene = async (sceneId: string, updates: any) => {
    await fetch(`http://localhost:8000/scenes/${sceneId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    loadScript();
  };

  const generateImage = async (sceneId: string) => {
    await fetch(`http://localhost:8000/scenes/${sceneId}/generate-image`, {
      method: "POST",
    });

    pollForImage(sceneId);
  };

  const pollForImage = async (sceneId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`http://localhost:8000/scenes/${sceneId}`);
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
        <button
          onClick={() => router.push(`/voice/${scriptId}`)}
          className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700"
        >
          Continue to Voice & Video
        </button>
      </div>
    </div>
  );
}
