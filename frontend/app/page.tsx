"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "../lib/api";

const SAMPLE_SCENES = [
  {
    title: "Opening Scene",
    description: "Introduce the concept with a bold visual.",
    image_path: "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=900&q=80",
    audio_path: "https://interactive-examples.mdn.mozilla.net/media/examples/t-rex-roar.mp3",
    style: "cinematic",
    duration_seconds: 8,
  },
  {
    title: "Key Point",
    description: "Summarize the main idea with text overlay.",
    image_path: "https://images.unsplash.com/photo-1515169067865-5387ec356754?auto=format&fit=crop&w=900&q=80",
    audio_path: "https://interactive-examples.mdn.mozilla.net/media/examples/t-rex-roar.mp3",
    style: "animated",
    duration_seconds: 7,
  },
  {
    title: "Closing Scene",
    description: "Finish with a clean call to action.",
    image_path: "https://images.unsplash.com/photo-1496307042754-b4aa456c4a2d?auto=format&fit=crop&w=900&q=80",
    audio_path: "https://interactive-examples.mdn.mozilla.net/media/examples/t-rex-roar.mp3",
    style: "faceless_broll",
    duration_seconds: 6,
  },
];

export default function HomePage() {
  const router = useRouter();
  const [scripts, setScripts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const loadScripts = async () => {
    const res = await fetch(`${API_BASE_URL}/scripts`);
    const data = await res.json();
    setScripts(data);
    setLoading(false);
  };

  useEffect(() => {
    loadScripts();
  }, []);

  const createScriptWithScenes = async () => {
    setCreating(true);
    try {
      const createScriptRes = await fetch(`${API_BASE_URL}/scripts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "My AI Video Script", description: "Generated sample script with scenes." }),
      });
      const script = await createScriptRes.json();

      await Promise.all(
        SAMPLE_SCENES.map((scene) =>
          fetch(`${API_BASE_URL}/scenes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...scene, script_id: script.id }),
          })
        )
      );

      router.push(`/script/${script.id}`);
    } catch (error) {
      console.error("Script creation failed", error);
      setCreating(false);
    }
  };

  const openScript = (scriptId: string) => {
    router.push(`/script/${scriptId}`);
  };

  return (
    <main className="max-w-5xl mx-auto py-12 px-6">
      <section className="bg-white rounded-3xl shadow-sm p-10 mb-10">
        <h1 className="text-4xl font-bold mb-4">AI Video Studio</h1>
        <p className="text-slate-600 mb-6">
          Create or continue a script, then generate image, voice, and video assets using the connected backend.
        </p>
        <button
          onClick={createScriptWithScenes}
          disabled={creating}
          className="inline-flex items-center justify-center rounded-full bg-indigo-600 px-6 py-3 text-white shadow hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? "Creating script…" : "Create a Sample Script"}
        </button>
      </section>

      <section className="bg-white rounded-3xl shadow-sm p-10">
        <h2 className="text-2xl font-semibold mb-4">Existing Scripts</h2>
        {loading ? (
          <div className="text-slate-500">Loading scripts…</div>
        ) : scripts.length === 0 ? (
          <div className="text-slate-500">No scripts found. Create one above to get started.</div>
        ) : (
          <div className="space-y-4">
            {scripts.map((script) => (
              <button
                key={script.id}
                onClick={() => openScript(script.id)}
                className="w-full text-left rounded-2xl border border-slate-200 p-5 hover:border-indigo-500 hover:bg-slate-50"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold">{script.title}</h3>
                    <p className="text-slate-500">{script.description ?? "No description"}</p>
                  </div>
                  <span className="text-indigo-600">Open</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
