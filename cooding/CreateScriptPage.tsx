"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function CreateScriptPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!title || !text) return alert("Please enter a title and script");

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/scripts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, text }),
      });

      const data = await res.json();

      router.push(`/script/${data.script_id}`);
    } catch (err) {
      console.error(err);
      alert("Error creating script");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold mb-6">Create New Video</h1>

      <div className="space-y-4">
        <div>
          <label className="block font-medium mb-1">Title</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2"
            placeholder="My Video Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Script</label>
          <textarea
            className="w-full border rounded px-3 py-2 h-64"
            placeholder="Paste your script here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Generate Scenes"}
        </button>
      </div>
    </div>
  );
}
