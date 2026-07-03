"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "../../../lib/api";

export default function RenderPage({ params }: { params: { scriptId: string } }) {
  const scriptId = params.scriptId;

  const [scenes, setScenes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [resolution, setResolution] = useState("1080p");
  const [musicStyle, setMusicStyle] = useState("cinematic");

  const [renderId, setRenderId] = useState<string | null>(null);
  const [renderStatus, setRenderStatus] = useState("idle");
  const [finalVideoUrl, setFinalVideoUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [sceneGenerating, setSceneGenerating] = useState<Record<string, boolean>>({});

  const [niche, setNiche] = useState("Social media ads");
  const [languageVoice, setLanguageVoice] = useState("English - Female");
  const [artStyle, setArtStyle] = useState("Comic");
  const [captionStyle, setCaptionStyle] = useState("Modern captions");
  const [effects, setEffects] = useState("None");
  const [socialAccounts, setSocialAccounts] = useState("");
  const [videoDuration, setVideoDuration] = useState(60);
  const [resolvedSettings, setResolvedSettings] = useState<any | null>(null);

  // Load scenes
  const loadScenes = async () => {
    setLoading(true);
    setErrorMessage("");
    try {
      const res = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);
      if (!res.ok) {
        throw new Error(`Failed to load script (${res.status})`);
      }

      const data = await res.json();
      setScenes(data.scenes ?? []);
      if (data.script?.settings) {
        const s = data.script.settings;
        setNiche(s.niche || niche);
        setLanguageVoice(s.language_voice || languageVoice);
        setArtStyle(s.art_style || artStyle);
        setCaptionStyle(s.caption_style || captionStyle);
        setEffects(s.effects || effects);
        setSocialAccounts(s.social_accounts || socialAccounts);
        setVideoDuration(s.duration_seconds ?? videoDuration);
      }
    } catch (error) {
      console.error("Failed to load scenes", error);
      setErrorMessage("Unable to load scenes. Please refresh the page.");
      setScenes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScenes();
  }, []);

  const startRender = async () => {
    setErrorMessage("");
    setRenderStatus("processing");

    try {
      const res = await fetch(`${API_BASE_URL}/render/${scriptId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          aspect_ratio: aspectRatio,
          resolution,
          music_style: musicStyle,
          niche,
          language_voice: languageVoice,
          background_music: musicStyle,
          art_style: artStyle,
          caption_style: captionStyle,
          effects,
          social_accounts: socialAccounts,
          duration_seconds: videoDuration,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || "Render request failed.");
      }

      const data = await res.json();
      setRenderId(data.render_id);
      setResolvedSettings(data.settings ?? null);
      pollForRender(data.render_id);
    } catch (error) {
      console.error("Render failed", error);
      setRenderStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Render failed.");
    }
  };

  const pollForRender = (id: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/render/${id}`);
        if (!res.ok) {
          throw new Error(`Render poll failed (${res.status})`);
        }

        const data = await res.json();
        setRenderStatus(data.status);

        if (data.status === "done") {
          setFinalVideoUrl(data.final_video_url ?? "");
          await loadScenes();
          clearInterval(interval);
        }

        if (data.status === "error") {
          setErrorMessage("Render failed during processing.");
          clearInterval(interval);
        }
      } catch (error) {
        console.error("Render poll failed", error);
        setRenderStatus("error");
        setErrorMessage(error instanceof Error ? error.message : "Render poll failed.");
        clearInterval(interval);
      }
    }, 3000);
  };

  if (loading) return <div className="p-6">Loading timeline...</div>;

  return (
    <div className="max-w-4xl mx-auto py-10 px-6">
      <h1 className="text-3xl font-bold mb-6">Final Render</h1>

      <p className="text-gray-600 mb-8">
        Review your clips, choose export settings, and render your final video.
      </p>

      {/* Timeline */}
      <div className="border rounded-lg p-4 bg-white shadow-sm mb-8">
        <h2 className="text-xl font-semibold mb-4">Timeline</h2>

        <div className="flex overflow-x-auto space-x-4">
          {scenes.length === 0 ? (
            <div className="text-gray-500 italic">No scenes found. Add a scene in the editor first.</div>
          ) : (
            scenes.map((scene, index) => (
              <div
                key={scene.id}
                className="min-w-[200px] border rounded p-2 bg-gray-50"
              >
                <p className="font-medium mb-2">Scene {index + 1}</p>

                {scene.video_url ? (
                  <video
                    src={scene.video_url}
                    className="w-full rounded"
                    muted
                    autoPlay
                    loop
                  />
                ) : (
                  <div className="text-gray-500 italic">No video generated</div>
                )}

                {!scene.video_url && (
                  <div className="mt-2">
                    <button
                      onClick={async () => {
                        setErrorMessage("");
                        setSceneGenerating((prev) => ({ ...prev, [scene.id]: true }));
                        try {
                          const response = await fetch(`${API_BASE_URL}/scenes/${scene.id}/generate-video`, {
                            method: "POST",
                          });
                          if (!response.ok) {
                            throw new Error("Video generation failed. Please try again.");
                          }
                          await loadScenes();
                        } catch (error) {
                          console.error("Scene video generation failed", error);
                          setErrorMessage(
                            error instanceof Error
                              ? error.message
                              : "Failed to generate scene video."
                          );
                        } finally {
                          setSceneGenerating((prev) => ({ ...prev, [scene.id]: false }));
                        }
                      }}
                      disabled={sceneGenerating[scene.id] || loading}
                      className="mt-2 bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {sceneGenerating[scene.id] ? "Generating..." : "Generate Video"}
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Render Settings */}
      <div className="border rounded-lg p-4 bg-white shadow-sm mb-8">
        <h2 className="text-xl font-semibold mb-4">Export Settings</h2>

        {/* Aspect Ratio */}
        <label className="block font-medium">Aspect Ratio</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={aspectRatio}
          onChange={(e) => setAspectRatio(e.target.value)}
        >
          <option value="9:16">Vertical (9:16)</option>
          <option value="16:9">Horizontal (16:9)</option>
          <option value="1:1">Square (1:1)</option>
        </select>

        {/* Resolution */}
        <label className="block font-medium">Resolution</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={resolution}
          onChange={(e) => setResolution(e.target.value)}
        >
          <option value="720p">720p</option>
          <option value="1080p">1080p</option>
        </select>

        {/* Niche */}
        <label className="block font-medium">Automated niche</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={niche}
          onChange={(e) => setNiche(e.target.value)}
        >
          <option value="AI choose best niche">AI choose best niche</option>
          <option value="Social media ads">Social media ads</option>
          <option value="Personal branding">Personal branding</option>
          <option value="Product launch">Product launch</option>
          <option value="Education & tutorials">Education & tutorials</option>
          <option value="Entertainment">Entertainment</option>
        </select>

        {/* Language & Voice */}
        <label className="block font-medium">Automated language & voice</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={languageVoice}
          onChange={(e) => setLanguageVoice(e.target.value)}
        >
          <option value="AI choose best voice">AI choose best voice</option>
          <option value="English - Female">English - Female</option>
          <option value="English - Male">English - Male</option>
          <option value="Spanish - Female">Spanish - Female</option>
          <option value="Japanese - Neutral">Japanese - Neutral</option>
        </select>

        {/* Background Music */}
        <label className="block font-medium">Automated background music</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={musicStyle}
          onChange={(e) => setMusicStyle(e.target.value)}
        >
          <option value="AI choose music">AI choose music</option>
          <option value="cinematic">Cinematic</option>
          <option value="chill">Chill</option>
          <option value="upbeat">Upbeat</option>
          <option value="ambient">Ambient</option>
          <option value="none">None</option>
        </select>

        {/* Art Style */}
        <label className="block font-medium">Automated art style</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={artStyle}
          onChange={(e) => setArtStyle(e.target.value)}
        >
          <option value="AI choose style">AI choose style</option>
          <option value="Comic">Comic</option>
          <option value="Anime">Anime</option>
          <option value="Cinematic">Cinematic</option>
          <option value="Minimal">Minimal</option>
          <option value="Retro">Retro</option>
        </select>

        {/* Caption Style */}
        <label className="block font-medium">Automated caption style</label>
        <select
          className="w-full border rounded px-3 py-2 mb-4"
          value={captionStyle}
          onChange={(e) => setCaptionStyle(e.target.value)}
        >
          <option value="AI choose caption style">AI choose caption style</option>
          <option value="Modern captions">Modern captions</option>
          <option value="Bold title cards">Bold title cards</option>
          <option value="Minimal subtitles">Minimal subtitles</option>
          <option value="Retro captions">Retro captions</option>
        </select>

        {/* Effects */}
        <label className="block font-medium">Effects</label>
        <select
          className="w-full border rounded px-3 py-2 mb-2"
          value={effects}
          onChange={(e) => setEffects(e.target.value)}
        >
          <option value="None">None</option>
          <option value="Glitch">Glitch effect</option>
          <option value="VHS">VHS style</option>
          <option value="Cinematic glow">Cinematic glow</option>
          <option value="Retro scanline">Retro scanline</option>
        </select>
        <p className="text-sm text-gray-500 mb-4">
          Glitch effect: Glitches the subject with chromatic distortion and eerie shake — perfect for horror, thrillers, and scary content.
        </p>

        {/* Social Accounts */}
        <label className="block font-medium">Connect Social Accounts</label>
        <input
          className="w-full border rounded px-3 py-2 mb-4"
          value={socialAccounts}
          onChange={(e) => setSocialAccounts(e.target.value)}
          placeholder="Add Instagram, TikTok, LinkedIn handles"
        />

        {/* Video Duration */}
        <label className="block font-medium">Video Duration (seconds)</label>
        <input
          type="number"
          className="w-full border rounded px-3 py-2 mb-4"
          value={videoDuration}
          readOnly
        />
      </div>

      {/* Render Button */}
      {/* Automation Profile Preview */}
      <div className="mt-6 border rounded p-4 bg-gray-50">
        <h3 className="text-lg font-semibold mb-2">Automation Profile Preview</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="font-medium">Current selections</p>
            <p>Niche: {niche}</p>
            <p>Language & Voice: {languageVoice}</p>
            <p>Music: {musicStyle}</p>
            <p>Art Style: {artStyle}</p>
            <p>Caption Style: {captionStyle}</p>
            <p>Effects: {effects}</p>
            <p>Social: {socialAccounts || '—'}</p>
            <p>Duration: {videoDuration}s</p>
          </div>
          <div>
            <p className="font-medium">Resolved by backend (if available)</p>
            {resolvedSettings ? (
              <div>
                <p>Niche: {resolvedSettings.niche}</p>
                <p>Language & Voice: {resolvedSettings.language_voice}</p>
                <p>Music: {resolvedSettings.background_music}</p>
                <p>Art Style: {resolvedSettings.art_style}</p>
                <p>Caption Style: {resolvedSettings.caption_style}</p>
                <p>Effects: {resolvedSettings.effects}</p>
                <p>Social: {resolvedSettings.social_accounts ?? '—'}</p>
                <p>Duration: {resolvedSettings.duration_seconds}s</p>
              </div>
            ) : (
              <p className="text-gray-500">Render not started — backend defaults will appear here.</p>
            )}
          </div>
        </div>
      </div>

      <button
        onClick={startRender}
        disabled={loading || scenes.length === 0 || renderStatus === "processing"}
        className="mt-4 bg-purple-600 text-white px-6 py-3 rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {renderStatus === "processing" ? "Rendering..." : "Render Final Video"}
      </button>

      {errorMessage && (
        <div className="mt-6 rounded border border-red-300 bg-red-50 p-4 text-red-700">
          {errorMessage}
        </div>
      )}

      {/* Render Status */}
      {renderStatus !== "idle" && (
        <div className="mt-6">
          <p className="text-lg font-medium">
            Status:{" "}
            <span className="text-blue-600 capitalize">{renderStatus}</span>
          </p>
          {renderStatus === "done" && (
            <div className="mt-4 rounded bg-green-50 border border-green-200 p-3 text-green-800">
              Render complete — your final video is ready. You can download it below.
            </div>
          )}
        </div>
      )}

      {/* Final Video */}
      {finalVideoUrl && (
        <div className="mt-10">
          <h2 className="text-xl font-semibold mb-4">Final Video</h2>
          <video controls src={finalVideoUrl} className="w-full rounded" />
          <a
            href={finalVideoUrl}
            download
            className="mt-4 inline-block bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700"
          >
            Download Video
          </a>
        </div>
      )}
    </div>
  );
}
