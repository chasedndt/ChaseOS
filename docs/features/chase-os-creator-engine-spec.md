# ChaseOS Creator Engine — Recordly/OpenScreen Integration Spec

**Document purpose:** Repository-ready context file for Claude Code, Codex, or another implementation agent to inspect inside the ChaseOS repository before implementation.

**Date prepared:** 2026-05-19  
**Product name:** ChaseOS  
**Module name:** `chase_creator_engine`  
**Immediate implementation target:** Option 1 — transcript / voice-note / context-prompt driven workflow  
**Later roadmap:** Option 2 — raw screen recording + AI video understanding + prompt-to-edit pipeline  
**Primary recorder/editor target:** Recordly  
**Secondary future recorder/editor target:** OpenScreen  
**Out of scope:** OpenHuman. This module should integrate with ChaseOS, Hermes Agent, and OpenClaw only.

---

## 1. Executive Summary

ChaseOS needs a content-creation workflow module that turns recorded product demos, build videos, repo reviews, and screen walkthroughs into publishable content packages.

The core idea is not to create fake AI videos. The creator still records the real demo. ChaseOS handles the slow production work:

- transcript generation
- transcript cleanup
- AI voiceover script drafting
- optional AI voiceover audio
- subtitles / captions
- edit plan generation
- social pack generation
- repo/document context retrieval through RAG
- project memory storage
- eventual integration with Recordly/OpenScreen timeline editing

The first version should not try to fully understand and edit a video autonomously. It should start with the user supplying context through one of these:

1. a rough transcript
2. a voice note
3. a short written context prompt
4. the audio already inside the video recording

Then ChaseOS produces a structured creator package.

The later version should analyse the video visually, detect what is happening on screen, retrieve repo/document context, and generate the transcript, captions, voiceover, edit plan, and publishing assets with minimal user input.

---

## 2. Corrected Product Context

The product is **ChaseOS**, not ChaseOS.

The open-source recorder currently in use is **Recordly**.

OpenScreen is still relevant because:

- Recordly originally started as a fork of OpenScreen.
- OpenScreen has a proposed local MCP server feature that maps closely to the agent-controlled editor surface ChaseOS needs later.
- OpenScreen has a more permissive MIT license.

However, for the current build, Recordly is the stronger immediate integration target because it already has deeper wiring for captions, Whisper runtime support, FFmpeg/export handling, native capture helpers, project/session management, a media server, and a permission-gated extension API.

---

## 3. Scope Lock

### In scope for MVP

- Recordly-exported or OBS-exported MP4/WebM/MOV ingestion
- watch-folder ingestion
- manual upload/file selection ingestion
- audio extraction
- transcription
- cleaned transcript generation
- AI narration script generation
- caption generation as SRT/VTT/ASS
- optional TTS voiceover generation
- social pack generation
- RAG context pack from repo/docs/notes/brand memory
- storage of job outputs inside ChaseOS
- review-first workflow
- Hermes/OpenClaw callable tools for starting/checking jobs

### In scope for future integration

- Recordly bridge / local agent server
- OpenScreen bridge / MCP once implemented or forked
- timeline state reading
- region CRUD for trims/zooms/speed/annotations/blur
- canvas/aspect/webcam/layout settings
- frame capture at timestamps
- auto-short generation
- auto-upload after approval
- performance feedback loop

### Out of scope

- OpenHuman
- custom model training in MVP
- fully autonomous publishing without review
- attempting to control Recordly/OpenScreen through brittle UI automation as the primary integration
- blindly trusting transcripts without review
- direct modification of AGPL Recordly code without license/compliance review

---

## 4. External Project Snapshot

This section captures the current backend wiring of Recordly and OpenScreen for implementation planning.

### 4.1 Recordly Snapshot

**Repository:** `webadderallorg/Recordly`  
**Website:** `recordly.dev`  
**License:** AGPL 3.0  
**Stack:** Electron, React, TypeScript, Vite, PixiJS, dnd-timeline, FFmpeg, Whisper runtime, native capture helpers.

Recordly is a desktop app for polished screen recording and editing. Its README describes it as a desktop app for recording and editing screen captures with motion-driven presentation tools. It runs on macOS, Windows, and Linux. Platform capture notes:

- macOS uses native ScreenCaptureKit-based capture helpers.
- Windows uses a native Windows Graphics Capture helper on supported builds, with native WASAPI audio support.
- Linux records through Electron capture APIs.

Recordly core feature areas include:

- auto zooms
- cursor polish
- styled frames/backgrounds
- dynamic webcam bubble overlays
- timeline editing
- cursor/click effects
- export tooling
- captions / Whisper support
- extension API

#### 4.1.1 Recordly package wiring

`package.json` shows:

- package name: `recordly`
- version observed: `1.3.0-beta.3`
- app main entry: `dist-electron/main.cjs`
- build scripts for native helpers
- build script for Whisper runtime
- build scripts for Windows capture, Windows GPU export, NVIDIA CUDA compositor, cursor monitor
- dependencies including:
  - `ffmpeg-static`
  - `ffprobe-static`
  - `capturekit`
  - `uiohook-napi`
  - `electron-updater`
- app/editor dependencies including:
  - `pixi.js`
  - `pixi-filters`
  - `mediabunny`
  - `mp4box`
  - `web-demuxer`
  - `dnd-timeline`
  - `vite-plugin-electron`
  - `react`
  - `typescript`

This means Recordly is already much closer to the MVP target than OpenScreen because Recordly has local transcription/caption primitives and a modular IPC backend.

#### 4.1.2 Recordly backend folder structure

Observed important folders:

```text
Recordly/
  electron/
    appPaths.ts
    cursorHider.ts
    main.ts
    mediaServer.ts
    preload.ts
    rendererServer.ts
    updater.ts
    windows.ts
    ipc/
      captions/
      cursor/
      export/
      ffmpeg/
      paths/
      project/
      recording/
      register/
      constants.ts
      handlers.ts
      nativeVideoExport.ts
      state.ts
      types.ts
      utils.ts
      windowsCaptureSelection.ts
  src/
    components/
    contexts/
    hooks/
    lib/
      exporter/
      extensions/
      geometry/
      appSettings.ts
      mediaTiming.ts
      shortcuts.ts
      utils.ts
      wallpapers.ts
```

#### 4.1.3 Recordly IPC handler model

`electron/ipc/handlers.ts` registers the key backend surfaces:

- sources
- recording
- permissions
- assets
- export
- captions
- project
- settings

That modularity is important. ChaseOS should not scrape the UI. If we fork or patch Recordly, the correct integration layer is to add a local bridge that calls these existing handlers or mirrors their command shape.

#### 4.1.4 Recordly recording backend

The recording handler wiring includes:

- native Windows capture path using Windows Graphics Capture
- macOS native capture path using ScreenCaptureKit
- fallback/browser-side microphone capture handling
- FFmpeg capture handling
- cursor telemetry sampling and persistence
- recording diagnostics
- validation of recorded video
- sidecar audio handling for system/microphone audio

Important MVP implication:

- ChaseOS can initially treat Recordly as the capture app and ingest exported/recorded files.
- Later, ChaseOS can request current video/session state and timeline edit operations through a Recordly bridge.

#### 4.1.5 Recordly captions backend

Recordly already has a caption handler that exposes:

- video file picker
- audio file picker
- Whisper executable picker
- Whisper model picker
- Whisper small model status
- Whisper small model download
- Whisper small model delete
- auto-caption generation

The caption generator:

1. resolves a Whisper executable
2. resolves a Whisper model
3. extracts audio from the video using FFmpeg
4. converts audio to mono 16k WAV
5. runs Whisper
6. parses JSON or SRT output
7. returns timed cues

This is directly aligned with ChaseOS Option 1.

#### 4.1.6 Recordly project/session backend

Recordly project handlers include:

- reveal in folder
- open recordings folder
- get/set recordings directory
- save/load project files
- list project files
- open project at path
- set current video path
- set current recording session
- get current recording session
- get current video path
- delete recording file
- get local media URL through the media server

Important MVP implication:

- ChaseOS can ingest Recordly recordings from the recordings directory.
- Later ChaseOS can interact with Recordly projects if we expose a safe bridge or add an adapter inside a fork.

#### 4.1.7 Recordly export backend

Recordly export handlers include:

- native video export start
- native video frame writing
- hardware-accelerated video encoding detection/resolution
- FFmpeg export arguments
- temp-file streaming
- owned export path handling
- static layout export
- audio muxing

Important future implication:

- ChaseOS should generate an edit plan first.
- Recordly should execute the edit plan if/when the bridge is implemented.
- For MVP, ChaseOS can render captions/voiceover itself with FFmpeg and leave Recordly rendering untouched.

#### 4.1.8 Recordly extension API

Recordly has an extension API. Extensions run in the editor renderer and use a permission-gated host API.

Extension permissions include:

- `render`
- `cursor`
- `audio`
- `timeline`
- `ui`
- `assets`
- `export`

Extension capabilities include:

- render hooks
- cursor effects
- frame registration
- wallpaper registration
- cursor style registration
- settings panels
- playback/timeline events
- export lifecycle events
- read-only queries such as video info, cursor at time, zoom state, playback state, canvas dimensions, active frame, aspect ratio

Important implication:

- Recordly extensions are useful for overlays and editor-side UI panels.
- They do **not** appear to be enough by themselves for full agent editing because the public extension API is mostly render/timeline event/read-only oriented.
- The best future bridge is probably **Recordly local HTTP/MCP server + internal IPC/edit-state commands**, not only an extension.

#### 4.1.9 Recordly licensing risk

Recordly is AGPL 3.0. Do not copy Recordly code directly into a closed ChaseOS codebase without license review.

Safer integration options:

1. Treat Recordly as an external user-installed app and ingest files from it.
2. Build a separate open-source Recordly bridge/plugin under compatible licensing.
3. Keep ChaseOS adapter code independent and communicate over a local process boundary.
4. If forking Recordly, comply with AGPL obligations.

This is not legal advice, but implementation agents should not ignore this.

---

### 4.2 OpenScreen Snapshot

**Repository:** `siddharthvaddem/openscreen`  
**License:** MIT  
**Stack:** Electron, React, TypeScript, Vite, PixiJS, dnd-timeline.

OpenScreen is a free open-source alternative to Screen Studio. Its README explicitly warns that it started as a side project and is not production grade. It still has valuable architecture and a permissive license.

OpenScreen core features include:

- window/region/full-screen capture
- microphone and system audio
- webcam overlay
- auto/manual zooms
- backgrounds
- motion blur
- crop/trim/speed control
- blur effects
- cursor/click highlighting
- text/arrow/image annotations
- saved projects
- MP4/GIF export

#### 4.2.1 OpenScreen package wiring

Observed package details:

- package name: `openscreen`
- version observed: `1.4.0`
- app main entry: `dist-electron/main.js`
- build scripts for macOS native helper
- build scripts for Windows WGC helper
- Electron + Vite + TypeScript build
- dependencies include PixiJS, dnd-timeline, mediabunny, mp4box, web-demuxer, cursor/canvas/editor dependencies

#### 4.2.2 OpenScreen backend folder structure

Observed important folders:

```text
openscreen/
  electron/
    ipc/
      handlers.ts
    native-bridge/
    native/
    main.ts
    preload.ts
    windows.ts
  src/
    lib/
      cursor/
      exporter/
      blurEffects.ts
      compositeLayout.ts
      cursorTelemetryBuffer.ts
      nativeMacRecording.ts
      nativeWindowsRecording.ts
      recordingSession.ts
      userPreferences.ts
      wallpaper.ts
```

OpenScreen appears less modular in IPC than Recordly. Its main IPC surface is concentrated in `electron/ipc/handlers.ts`, while Recordly has more separated handler modules.

#### 4.2.3 OpenScreen MCP status

OpenScreen has an open issue proposing a local MCP/HTTP server. It is not currently implemented in the observed repository state.

The proposed MCP server would be opt-in, off by default, and expose editor operations such as:

- read editor state
- read timeline summary
- region CRUD for zoom, trim, speed, annotation, blur
- canvas settings
- seek/playhead query
- raw source frame capture at a timestamp
- composited rendered frame capture at a timestamp

The proposal explicitly says every write should go through `pushState`, so each agent action becomes an undo checkpoint.

Important conclusion:

- Do **not** plan on integrating an existing OpenScreen MCP server as if it already ships.
- The correct plan is either:
  1. wait for OpenScreen MCP to land, then integrate, or
  2. build a ChaseOS-compatible bridge/fork based on the proposal.

---

## 5. Recordly vs OpenScreen Integration Recommendation

### Immediate recommendation

Use **Recordly as the primary MVP integration target**.

Reasons:

- User is already using Recordly.
- Recordly already has Whisper/caption backend wiring.
- Recordly already has FFmpeg/audio extraction wiring.
- Recordly already has project/session/media-server handlers.
- Recordly has a modular IPC backend that can be extended.
- Recordly is more aligned with Option 1.

### Secondary recommendation

Keep **OpenScreen compatibility as an adapter target**, not the first build.

Reasons:

- OpenScreen has MIT licensing.
- OpenScreen has strong editor primitives.
- OpenScreen MCP proposal is almost exactly the future agent editing surface ChaseOS needs.
- OpenScreen is not currently as ready for Option 1 because Recordly already has the captions/Whisper path.

### Adapter strategy

Do not build ChaseOS directly around Recordly internals. Build a provider interface:

```ts
export interface CaptureEditorProvider {
  id: "recordly" | "openscreen" | "obs" | "manual";
  label: string;
  detect(): Promise<ProviderStatus>;
  listRecordings?(): Promise<RecordingAsset[]>;
  listProjects?(): Promise<CaptureProject[]>;
  importRecording(input: ImportRecordingInput): Promise<ImportedRecording>;
  getProjectState?(projectId: string): Promise<CaptureProjectState>;
  applyEditPlan?(projectId: string, editPlan: EditPlan): Promise<ApplyEditPlanResult>;
  addCaptions?(projectId: string, captions: CaptionCue[]): Promise<ApplyCaptionsResult>;
  exportVideo?(projectId: string, options: ExportOptions): Promise<ExportResult>;
}
```

Provider priority:

1. `recordly` — MVP external-file ingestion first, bridge later.
2. `obs` — fallback file ingestion only.
3. `manual` — upload/drag-drop ingestion.
4. `openscreen` — future bridge/MCP adapter.

---

## 6. ChaseOS Creator Engine Architecture

### 6.1 High-level architecture

```text
Recordly / OBS / OpenScreen recording
        |
        v
ChaseOS Creator Intake
        |
        +--> extract audio
        +--> transcribe audio
        +--> ingest user voice note / context prompt
        +--> retrieve RAG context
        +--> generate script
        +--> generate captions
        +--> generate optional voiceover
        +--> generate edit plan
        +--> render MVP output through FFmpeg
        +--> save final assets
        +--> generate social pack
        +--> create content memory card
        |
        v
Hermes / OpenClaw tools for orchestration, approval, and status
```

### 6.2 MVP architecture

MVP should be file-driven.

```text
Recordly exports video
        |
        v
ChaseOS watches recordings folder OR user selects file
        |
        v
Creator job is created
        |
        v
Audio extracted with FFmpeg
        |
        v
Whisper transcription
        |
        v
RAG context pack built from prompt + repo/docs/brand memory
        |
        v
Script/captions/social pack generated
        |
        v
Optional TTS voiceover generated
        |
        v
Captions/voiceover rendered or prepared for review
        |
        v
Human approval
        |
        v
Final package saved
```

### 6.3 Future architecture

Future version should be editor-bridge driven.

```text
Recordly/OpenScreen editor session
        |
        v
Local bridge / MCP / HTTP server
        |
        v
ChaseOS Creator Agent
        |
        +--> read timeline
        +--> sample frames
        +--> OCR/source understanding
        +--> retrieve repo/docs context
        +--> generate edit plan
        +--> apply trims/zooms/captions/annotations
        +--> export
        |
        v
Human review + approval
```

---

## 7. Proposed Repository Structure

The implementation agent should adapt this to the actual ChaseOS repo conventions. If ChaseOS is a monorepo, this should become a package/module rather than scattered code.

Suggested structure:

```text
chase-os/
  docs/
    creator-engine/
      chase-os-creator-engine-spec.md
      rag-implementation-notes.md
      recordly-integration-notes.md
      openscreen-roadmap.md

  src/
    modules/
      creator-engine/
        index.ts
        types.ts
        constants.ts
        README.md

        adapters/
          index.ts
          CaptureEditorProvider.ts
          recordly/
            RecordlyProvider.ts
            recordlyPaths.ts
            recordlyProject.ts
            recordlyBridgeClient.ts
          openscreen/
            OpenScreenProvider.ts
            openscreenMcpClient.ts
          obs/
            ObsProvider.ts
          manual/
            ManualUploadProvider.ts

        pipeline/
          createCreatorJob.ts
          ingestRecording.ts
          extractAudio.ts
          transcribeAudio.ts
          normalizeTranscript.ts
          generateScript.ts
          generateCaptions.ts
          generateVoiceover.ts
          generateEditPlan.ts
          renderOutput.ts
          generateSocialPack.ts
          saveMemoryCard.ts

        rag/
          index.ts
          sources/
            githubSource.ts
            docsSource.ts
            notesSource.ts
            brandMemorySource.ts
            transcriptSource.ts
            frameOcrSource.ts
          chunking/
            chunkMarkdown.ts
            chunkCode.ts
            chunkTranscript.ts
          retrieval/
            vectorSearch.ts
            keywordSearch.ts
            hybridSearch.ts
            rerank.ts
          contextPack.ts

        prompts/
          scriptPrompt.ts
          transcriptCleanupPrompt.ts
          captionsPrompt.ts
          voiceoverPrompt.ts
          editPlanPrompt.ts
          socialPackPrompt.ts
          memoryCardPrompt.ts

        tts/
          TtsProvider.ts
          localTtsProvider.ts
          apiTtsProvider.ts

        transcription/
          TranscriptionProvider.ts
          whisperCppProvider.ts
          fasterWhisperProvider.ts
          apiWhisperProvider.ts

        rendering/
          ffmpegRender.ts
          captionBurnIn.ts
          audioMux.ts
          exportProfiles.ts

        storage/
          creatorJobStore.ts
          assetStore.ts
          contentVault.ts

        tools/
          hermesTools.ts
          openclawTools.ts
          mcpTools.ts

        ui/
          CreatorEnginePage.tsx
          CreatorJobList.tsx
          CreatorJobDetail.tsx
          TranscriptEditor.tsx
          ScriptEditor.tsx
          CaptionReview.tsx
          SocialPackReview.tsx
```

If ChaseOS already has a Feature Manifest / Builder Studio architecture, add this module through a feature manifest.

Suggested feature manifest:

```json
{
  "id": "chase.creator_engine",
  "name": "Creator Engine",
  "version": "0.1.0",
  "type": "module",
  "routes": [
    {
      "path": "/creator",
      "label": "Creator Engine",
      "component": "CreatorEnginePage"
    }
  ],
  "permissions": [
    "filesystem.read.recordings",
    "filesystem.write.creator_assets",
    "ai.generate.text",
    "ai.transcribe.audio",
    "ai.embed.documents",
    "media.render.ffmpeg"
  ],
  "tools": [
    "creator.create_job",
    "creator.ingest_recording",
    "creator.transcribe",
    "creator.generate_script",
    "creator.generate_captions",
    "creator.generate_social_pack",
    "creator.render_preview",
    "creator.approve_package"
  ],
  "adapters": ["recordly", "obs", "manual", "openscreen"]
}
```

---

## 8. Core Data Models

### 8.1 CreatorJob

```ts
export type CreatorJobStatus =
  | "created"
  | "ingested"
  | "audio_extracted"
  | "transcribed"
  | "rag_ready"
  | "script_drafted"
  | "voiceover_ready"
  | "captions_ready"
  | "edit_plan_ready"
  | "rendered"
  | "social_pack_ready"
  | "review_required"
  | "approved"
  | "published"
  | "archived"
  | "failed";

export interface CreatorJob {
  id: string;
  title?: string;
  status: CreatorJobStatus;
  createdAt: string;
  updatedAt: string;
  sourceProvider: "recordly" | "openscreen" | "obs" | "manual";
  sourceVideoPath: string;
  sourceProjectPath?: string | null;
  contextPrompt?: string | null;
  voiceNotePath?: string | null;
  targetFormats: TargetFormat[];
  brandProfileId: "chasing_tech" | string;
  ragContextPackId?: string | null;
  outputs: CreatorJobOutputs;
  review: ReviewState;
  metadata: CreatorJobMetadata;
}
```

### 8.2 CreatorJobOutputs

```ts
export interface CreatorJobOutputs {
  extractedAudioPath?: string;
  transcriptPath?: string;
  cleanedTranscriptPath?: string;
  scriptPath?: string;
  voiceoverPath?: string;
  captionsSrtPath?: string;
  captionsVttPath?: string;
  captionsAssPath?: string;
  editPlanPath?: string;
  renderedVideoPath?: string;
  shortVideoPaths?: string[];
  socialPackPath?: string;
  memoryCardPath?: string;
}
```

### 8.3 TranscriptSegment

```ts
export interface TranscriptSegment {
  id: string;
  startMs: number;
  endMs: number;
  text: string;
  confidence?: number;
  speaker?: string;
  source: "video_audio" | "voice_note" | "manual";
  needsReview?: boolean;
}
```

### 8.4 CaptionCue

```ts
export interface CaptionCue {
  id: string;
  startMs: number;
  endMs: number;
  text: string;
  style?: "default" | "hook" | "keyword" | "code" | "warning";
  sourceSegmentIds?: string[];
}
```

### 8.5 EditPlan

```ts
export interface EditPlan {
  version: "0.1";
  jobId: string;
  intent: string;
  targetFormat: TargetFormat;
  edits: EditAction[];
  qualityChecks: EditPlanQualityCheck[];
}

export type EditAction =
  | TrimEditAction
  | ZoomEditAction
  | SpeedEditAction
  | CaptionEditAction
  | AnnotationEditAction
  | BlurEditAction
  | AudioEditAction
  | LayoutEditAction;
```

Example edit plan:

```json
{
  "version": "0.1",
  "jobId": "content_2026_05_19_recordly_demo",
  "intent": "Turn the raw Recordly demo into a Chasing Tech explainer",
  "targetFormat": "youtube_long",
  "edits": [
    {
      "type": "trim",
      "startMs": 0,
      "endMs": 2300,
      "reason": "dead air before demo starts"
    },
    {
      "type": "caption",
      "startMs": 0,
      "endMs": 4500,
      "text": "This is how ChaseOS turns demos into content packages.",
      "style": "hook"
    },
    {
      "type": "zoom",
      "startMs": 5200,
      "endMs": 11800,
      "target": { "x": 0.42, "y": 0.31, "scale": 1.65 },
      "reason": "viewer needs to read the repository title"
    }
  ],
  "qualityChecks": [
    {
      "id": "captions-readable",
      "status": "pending",
      "description": "Captions should not exceed reading speed."
    }
  ]
}
```

### 8.6 RAG Context Pack

```ts
export interface RagContextPack {
  id: string;
  jobId: string;
  query: string;
  generatedAt: string;
  detectedTopics: string[];
  detectedRepos: GitHubRepoRef[];
  sourceCards: RagSourceCard[];
  facts: RagFact[];
  claimsToAvoid: string[];
  brandRules: BrandRule[];
  suggestedAngles: string[];
  citations: RagCitation[];
}
```

### 8.7 Content Memory Card

```ts
export interface ContentMemoryCard {
  id: string;
  jobId: string;
  title: string;
  topic: string;
  format: TargetFormat[];
  sourceVideoPath: string;
  finalAssets: string[];
  hook: string;
  summary: string;
  keyClaims: string[];
  sourcesUsed: string[];
  brandLessons: string[];
  reusableHooks: string[];
  reusableBrollIdeas: string[];
  approvedByUser: boolean;
  publishedUrls?: string[];
  performanceMetrics?: ContentPerformanceMetrics;
}
```

---

## 9. Option 1 MVP Workflow

### 9.1 User experience

The user records a demo in Recordly or OBS.

Then in ChaseOS, the user creates a Creator Engine job and provides one of:

```text
I am showing how Recordly can become the screen-capture layer for ChaseOS. Make this a Chasing Tech style build-video script. Explain why this saves hours, how transcript-driven voiceover works, and how RAG will later understand the video from repo context.
```

or uploads a voice note:

```text
Make this a short build log for Chasing Tech. Hook: Content creation is not slow because recording is hard; it is slow because post-production eats the day. Explain the new ChaseOS Creator Engine.
```

Then ChaseOS produces:

```text
outputs/
  transcript.raw.json
  transcript.clean.md
  script.voiceover.md
  voiceover.wav
  captions.srt
  captions.vtt
  captions.ass
  edit_plan.json
  final_preview.mp4
  youtube_title_options.md
  youtube_description.md
  shorts_caption.md
  x_thread.md
  linkedin_post.md
  thumbnail_text_options.md
  memory_card.md
```

### 9.2 MVP flow

```text
1. User records with Recordly.
2. User exports/saves video.
3. ChaseOS detects file in watch folder or receives upload.
4. User adds context prompt or voice note.
5. ChaseOS extracts audio.
6. ChaseOS transcribes audio.
7. ChaseOS cleans transcript.
8. ChaseOS creates RAG context pack.
9. ChaseOS drafts voiceover script.
10. ChaseOS generates captions.
11. ChaseOS optionally generates TTS voiceover.
12. ChaseOS generates edit plan.
13. ChaseOS optionally renders captions/voiceover into preview using FFmpeg.
14. User reviews.
15. ChaseOS saves final package and memory card.
```

### 9.3 MVP job creation payload

```json
{
  "sourceProvider": "recordly",
  "sourceVideoPath": "/Users/chase/Videos/Recordly/recording-2026-05-19.mp4",
  "contextPrompt": "Make this a Chasing Tech build log about integrating Recordly into ChaseOS Creator Engine.",
  "targetFormats": ["youtube_long", "youtube_short", "x_thread", "linkedin"],
  "brandProfileId": "chasing_tech",
  "options": {
    "generateVoiceover": true,
    "burnCaptionsIntoPreview": true,
    "requireReviewBeforePublish": true
  }
}
```

---

## 10. Option 2 Roadmap

Option 2 is the later high-leverage workflow:

```text
User records a raw screen demo without a prepared transcript.
User gives ChaseOS a short context prompt.
ChaseOS analyses the video visually and contextually.
ChaseOS writes the transcript/script/captions/edit plan automatically.
```

### 10.1 Option 2 required capabilities

- frame sampling
- scene-change detection
- OCR over sampled frames
- browser/editor/app detection
- GitHub repo URL detection
- terminal command detection
- cursor/click/action importance detection
- visual summary per segment
- repo/document RAG retrieval
- edit-plan generation
- bridge-based timeline edits in Recordly/OpenScreen

### 10.2 Option 2 timeline understanding object

```json
[
  {
    "startMs": 0,
    "endMs": 8000,
    "visualSummary": "Browser shows a GitHub repository landing page.",
    "detectedApps": ["browser", "github"],
    "detectedText": ["Recordly", "open-source screen recorder"],
    "suggestedNarration": "The content engine starts with real demos, not fake AI-generated footage.",
    "suggestedEdits": [
      { "type": "zoom", "target": "repo title" },
      { "type": "caption", "text": "Real demos. Automated post-production." }
    ]
  }
]
```

### 10.3 Option 2 stages

#### Stage 1 — passive visual indexing

- sample one frame every 1-2 seconds
- run OCR
- run visual summaries
- store frame summaries as searchable chunks

#### Stage 2 — prompt-to-script from video context

- combine prompt + OCR + transcript + repo RAG
- generate narration timeline
- generate captions

#### Stage 3 — edit plan generation

- generate zooms/callouts/trims based on action importance
- do not auto-apply yet
- user reviews edit plan

#### Stage 4 — bridge-based editor application

- implement Recordly local bridge or OpenScreen MCP/fork
- apply safe edits through undoable editor commands

#### Stage 5 — performance learning

- compare generated content with user edits and published metrics
- learn preferred hook types, caption density, pacing, and topic angles

---

## 11. RAG Layer Deep Dive

The RAG layer is the core intelligence layer. Without it, the AI will write generic scripts. With it, ChaseOS can explain repos, tools, codebases, and product demos with context.

### 11.1 What RAG means here

RAG means ChaseOS retrieves relevant knowledge before generating the script, captions, edit plan, or social pack.

Inputs:

- user context prompt
- transcript
- voice note
- detected repo URL
- detected website/docs
- OCR from frames in future Option 2
- ChaseOS brand memory
- previous scripts
- previous content performance

Outputs:

- facts to use
- facts to avoid
- source snippets
- suggested angles
- title/hook ideas
- technical explanations
- citations/source references for memory

### 11.2 RAG sources

For Chasing Tech / ChaseOS content, index these source categories:

```text
1. GitHub README files
2. GitHub docs folders
3. GitHub release notes
4. GitHub issues
5. GitHub pull requests
6. GitHub commit history
7. package.json / pyproject.toml / Cargo.toml / config files
8. official documentation pages
9. user notes
10. previous ChaseOS scripts
11. previous Chasing Tech posts
12. brand rules
13. content calendar
14. saved hooks
15. approved captions
16. rejected AI drafts
17. performance metrics
18. video transcripts
19. future frame OCR summaries
```

### 11.3 RAG storage design

If ChaseOS uses Postgres, use `pgvector`.

If ChaseOS is local-first or SQLite-based, use one of:

- SQLite + vector extension
- LanceDB
- Chroma
- local embeddings index

Do not over-engineer this first. MVP can start with a simple vector store + metadata filters.

Suggested tables:

```sql
creator_sources
  id
  source_type
  uri
  title
  repo_owner
  repo_name
  branch
  fetched_at
  content_hash
  metadata_json

creator_chunks
  id
  source_id
  chunk_index
  text
  token_count
  embedding
  metadata_json

creator_rag_queries
  id
  job_id
  query
  created_at
  result_ids_json

creator_rag_context_packs
  id
  job_id
  context_pack_json
  created_at
```

### 11.4 Chunking rules

#### Markdown/docs

- chunk by headings
- preserve heading path
- include source URL/path
- keep chunks around 300-900 tokens

#### Code/config files

- chunk by function/class/module where possible
- for config files, chunk by top-level keys/sections
- preserve file path and language

#### GitHub issues/PRs

- separate original issue/PR body from comments
- preserve author, date, labels, status
- summarise long threads before embedding

#### Transcripts

- chunk by semantic segments, not arbitrary token size
- preserve timestamps
- preserve speaker/source

#### Frame OCR

- chunk by time window
- preserve frame timestamp and detected app/window

### 11.5 Retrieval strategy

Use hybrid retrieval:

```text
semantic vector search + keyword/BM25 + metadata filters + reranking
```

The query should be constructed from:

```text
context prompt
+ transcript summary
+ detected repo/tool names
+ target format
+ current script section being generated
```

Example retrieval query:

```text
Recordly ChaseOS Creator Engine screen recorder integration captions Whisper FFmpeg project session export IPC extension API
```

### 11.6 RAG context pack generation

The RAG layer should output a structured context pack before script generation:

```json
{
  "topic": "Integrating Recordly into ChaseOS Creator Engine",
  "detectedSources": [
    {
      "type": "github_repo",
      "name": "webadderallorg/Recordly",
      "confidence": 0.98
    }
  ],
  "facts": [
    {
      "claim": "Recordly has a caption backend that runs Whisper over FFmpeg-extracted audio.",
      "sourceId": "recordly-electron-ipc-captions-generate",
      "confidence": 0.92
    }
  ],
  "claimsToAvoid": [
    "Do not claim OpenScreen MCP is already implemented. It is currently an open feature request."
  ],
  "suggestedAngles": [
    "The bottleneck is not recording; it is post-production.",
    "ChaseOS should start with transcript-driven automation, then evolve to video understanding."
  ],
  "brandRules": [
    "Use direct, builder-focused language.",
    "Avoid generic AI hype."
  ]
}
```

### 11.7 RAG implementation phases

#### Phase RAG-0 — no vector database yet

- user prompt only
- source video transcript only
- brand profile only

#### Phase RAG-1 — local document retrieval

- index ChaseOS docs
- index saved scripts
- index brand rules
- index content calendar

#### Phase RAG-2 — GitHub repo retrieval

- fetch README/docs/releases/issues/PRs for mentioned repo
- chunk and embed
- generate repo fact sheet

#### Phase RAG-3 — video-aware retrieval

- OCR sampled frames
- detect repo/tool names from frame text
- use frame summaries as retrieval queries

#### Phase RAG-4 — feedback learning

- index approved vs rejected outputs
- index published metrics
- use this to improve future hooks, pacing, and social formats

---

## 12. AI Generation Components

### 12.1 Transcript cleanup

Input:

- raw transcript segments
- context prompt
- target format

Output:

- clean transcript
- uncertain words marked
- filler removed
- speaker intent preserved

Rules:

- do not invent facts
- keep technical terms intact
- mark uncertain sections
- preserve timestamps where possible

### 12.2 Voiceover script generation

Input:

- clean transcript
- user context prompt
- RAG context pack
- brand profile
- target duration

Output:

```text
script.voiceover.md
```

The script should include:

- hook
- intro/context
- explanation
- demo walkthrough
- why it matters
- call to action

### 12.3 Caption generation

Caption outputs:

- `.srt` for compatibility
- `.vtt` for web
- `.ass` for styled burn-in

Caption rules:

- keep captions short
- avoid too many words per screen
- emphasize key terms
- support 9:16 and 16:9 safe areas
- human review before final export

### 12.4 Voiceover generation

Voiceover providers should be abstracted:

```ts
export interface TtsProvider {
  id: string;
  synthesize(input: TtsInput): Promise<TtsOutput>;
}
```

Voiceover should be optional in MVP. Some videos may use the creator's own voice.

### 12.5 Social pack generation

Generate:

- YouTube title options
- YouTube description
- YouTube chapters if long-form
- YouTube tags/keywords
- Shorts/TikTok/Reels caption
- X thread
- LinkedIn post
- thumbnail text options
- pinned comment
- newsletter snippet if needed

---

## 13. Rendering Strategy

### 13.1 MVP rendering

Use ChaseOS / FFmpeg directly for MVP rendering.

MVP render jobs:

- mux original video + generated voiceover
- burn captions if requested
- export preview MP4
- generate short 9:16 crop if requested

Recordly itself does not need to be controlled for MVP rendering.

### 13.2 Future rendering

Use Recordly/OpenScreen editor bridge for:

- zooms
- trims
- speed changes
- annotations
- cursor effects
- webcam layout
- export profiles

### 13.3 Export profiles

```ts
export type TargetFormat =
  | "youtube_long"
  | "youtube_short"
  | "tiktok"
  | "instagram_reel"
  | "x_video"
  | "linkedin_video"
  | "internal_demo";
```

Profile examples:

```json
{
  "youtube_long": {
    "aspectRatio": "16:9",
    "resolution": "1920x1080",
    "captionSafeArea": "standard",
    "maxDurationSec": null
  },
  "youtube_short": {
    "aspectRatio": "9:16",
    "resolution": "1080x1920",
    "captionSafeArea": "vertical_center_lower_third",
    "maxDurationSec": 60
  }
}
```

---

## 14. Recordly Bridge Plan

### 14.1 MVP Recordly integration

Do not modify Recordly initially.

Implement:

- Recordly recordings folder detection
- import files from Recordly recordings folder
- optional user-selected Recordly project path
- metadata capture:
  - source path
  - file size
  - duration
  - created date
  - provider: `recordly`

### 14.2 Phase 2 Recordly bridge

Build a local bridge only after MVP proves useful.

Potential options:

1. **Recordly fork bridge**
   - Add a local HTTP/MCP server inside Recordly.
   - Expose editor state and edit commands.
   - Best technical route, but licensing/compliance needs care.

2. **Recordly extension + companion process**
   - Extension reads playback/timeline/export events.
   - Companion process talks to ChaseOS.
   - May be limited for write operations.

3. **Recordly project-file manipulation**
   - ChaseOS writes project JSON directly.
   - Risky unless project schema is stable and understood.

4. **External UI automation**
   - Do not use as primary route.
   - Too brittle.

### 14.3 Proposed Recordly bridge tools

```text
recordly.get_editor_state
recordly.get_timeline_summary
recordly.get_current_project
recordly.get_current_video_path
recordly.capture_frame
recordly.add_caption_region
recordly.add_zoom_region
recordly.add_trim_region
recordly.add_speed_region
recordly.add_annotation
recordly.add_blur_region
recordly.update_canvas_settings
recordly.seek
recordly.export_video
```

### 14.4 Security requirements

Bridge should be:

- disabled by default
- localhost only
- token-protected
- session-scoped
- explicit user approval for write operations
- undoable per action
- no arbitrary filesystem access
- no arbitrary command execution

---

## 15. OpenScreen MCP Roadmap

OpenScreen MCP is not implemented yet. It is an open feature request.

The proposed OpenScreen MCP is still highly relevant because it maps well to ChaseOS future needs.

### 15.1 Future integration path

```text
1. Track OpenScreen issue #574.
2. If merged, build OpenScreenProvider around the MCP URL.
3. If not merged, fork OpenScreen and implement a minimal local bridge.
4. Keep the same CaptureEditorProvider interface so ChaseOS does not care which editor is active.
```

### 15.2 Minimal OpenScreen-compatible tool surface

```text
openscreen.read_state
openscreen.timeline_summary
openscreen.capture_frame
openscreen.add_region
openscreen.update_region
openscreen.delete_region
openscreen.update_canvas
openscreen.seek
openscreen.export
```

### 15.3 Why OpenScreen still matters

- MIT license makes integration easier.
- Strong editor primitives.
- Existing proposal has the exact undoable-agent-editing concept needed later.
- Useful as a reference/fallback even if Recordly remains primary.

---

## 16. Hermes Integration

Hermes should be treated as the orchestration / execution agent layer.

### 16.1 Hermes role

Hermes can:

- start Creator Engine jobs
- monitor job status
- run scheduled automations
- invoke transcription/generation/rendering tools
- remember workflow lessons
- create reusable skills after repeated workflows
- notify user for review/approval

Hermes should **not** directly edit media files without going through ChaseOS Creator Engine tools.

### 16.2 Hermes tool surface

```ts
creator.create_job(input)
creator.ingest_recording(jobId)
creator.transcribe(jobId)
creator.build_rag_context(jobId)
creator.generate_script(jobId)
creator.generate_captions(jobId)
creator.generate_voiceover(jobId)
creator.generate_edit_plan(jobId)
creator.render_preview(jobId)
creator.generate_social_pack(jobId)
creator.request_review(jobId)
creator.approve(jobId)
creator.archive(jobId)
creator.get_status(jobId)
```

### 16.3 Hermes example command

```text
Create a Creator Engine job from the latest Recordly recording. Context: this is a build log about integrating Recordly into ChaseOS. Target YouTube long-form and Shorts. Generate the script, captions, social pack, and a review preview.
```

---

## 17. OpenClaw Integration

OpenClaw should be treated as a remote/chat control surface and agent ecosystem integration, not as the media-processing engine.

### 17.1 OpenClaw role

OpenClaw can:

- receive user commands from chat
- trigger ChaseOS Creator Engine tools
- ask for approvals
- provide status updates
- route tasks to Hermes/ChaseOS
- expose creator workflows through skills

OpenClaw should not receive broad filesystem or publishing permissions by default.

### 17.2 OpenClaw skill idea

Skill name:

```text
chase_creator_engine
```

Skill capabilities:

```text
- Create content job from latest Recordly export
- Add context prompt
- Generate script/captions/social pack
- Request approval
- Show output paths
```

### 17.3 Permission model

OpenClaw should only call ChaseOS tools. ChaseOS remains the authority for:

- file paths
- asset storage
- rendering
- review state
- publishing state

---

## 18. API / Tool Design

### 18.1 REST-style internal API

```http
POST /api/creator/jobs
GET  /api/creator/jobs
GET  /api/creator/jobs/:jobId
POST /api/creator/jobs/:jobId/ingest
POST /api/creator/jobs/:jobId/transcribe
POST /api/creator/jobs/:jobId/rag
POST /api/creator/jobs/:jobId/script
POST /api/creator/jobs/:jobId/captions
POST /api/creator/jobs/:jobId/voiceover
POST /api/creator/jobs/:jobId/edit-plan
POST /api/creator/jobs/:jobId/render-preview
POST /api/creator/jobs/:jobId/social-pack
POST /api/creator/jobs/:jobId/review
POST /api/creator/jobs/:jobId/approve
```

### 18.2 Event bus events

```text
creator.job.created
creator.job.ingested
creator.audio.extracted
creator.transcript.ready
creator.rag.ready
creator.script.ready
creator.captions.ready
creator.voiceover.ready
creator.edit_plan.ready
creator.preview.rendered
creator.social_pack.ready
creator.review.requested
creator.job.approved
creator.job.failed
```

### 18.3 CLI commands if ChaseOS has CLI

```bash
chase creator create --video ./demo.mp4 --context "Recordly integration build log"
chase creator transcribe <jobId>
chase creator generate <jobId> --script --captions --social
chase creator render <jobId> --preview
chase creator status <jobId>
```

---

## 19. UI Design

### 19.1 Creator Engine dashboard

Main UI sections:

- New Job
- Recent Recordly Recordings
- Active Jobs
- Review Queue
- Content Vault
- Brand Profiles
- RAG Sources
- Settings

### 19.2 Job detail page

Tabs:

1. Overview
2. Source Video
3. Transcript
4. RAG Context
5. Script
6. Captions
7. Voiceover
8. Edit Plan
9. Preview Render
10. Social Pack
11. Memory Card

### 19.3 Human review gates

Require approval for:

- final script
- final captions
- AI voiceover
- final rendered video
- social posts
- upload/publish action

---

## 20. Prompt Templates

### 20.1 Transcript cleanup prompt

```text
You are cleaning a transcript for a Chasing Tech creator workflow.

Inputs:
- Raw transcript with timestamps
- User context prompt
- Target format

Rules:
- Preserve meaning.
- Remove filler only when it does not change meaning.
- Keep technical terms.
- Mark unclear terms with [unclear: possible term].
- Do not invent facts.
- Output timestamped clean transcript.
```

### 20.2 Voiceover script prompt

```text
You are writing a voiceover script for Chasing Tech.

Use:
- Clean transcript
- User context prompt
- RAG context pack
- Brand rules

Style:
- Direct builder-focused tone.
- No generic AI hype.
- Explain why the tool/workflow matters.
- Make it feel like a real build log or technical demo, not an ad.

Output:
- Hook
- Voiceover script with timing sections
- Key visual cues
- Optional callouts
- CTA
```

### 20.3 Edit plan prompt

```text
Create a machine-readable edit plan.

Use:
- Transcript timestamps
- Video duration
- User context
- RAG context
- Target platform

Return JSON only.
Include:
- trims
- captions
- suggested zooms
- annotations
- blur suggestions if sensitive info is likely
- speed changes
- reasoning per edit

Do not include edits that require unsupported editor features.
```

### 20.4 Social pack prompt

```text
Generate a social publishing package for Chasing Tech.

Use:
- Final script
- RAG context pack
- Target platforms
- Brand voice

Output:
- YouTube title options
- YouTube description
- Chapters if applicable
- Shorts/Reels/TikTok caption
- X thread
- LinkedIn post
- Thumbnail text options
- Pinned comment
```

---

## 21. Quality Gates

### 21.1 Transcript quality

- Mark low-confidence sections.
- Do not publish captions without review.
- Flag likely hallucinated transcript sections.
- Check for technical term drift.

### 21.2 RAG quality

- Source facts from indexed docs where possible.
- Separate retrieved facts from inferred commentary.
- Do not claim a feature exists if it is only an issue/proposal.
- Store citations/source IDs in memory card.

### 21.3 Video quality

- Captions readable on mobile.
- Voiceover not clipped.
- Audio levels normalized.
- No private info visible.
- Export profile matches target platform.

### 21.4 Safety/security

- No arbitrary command execution from Hermes/OpenClaw.
- No unapproved filesystem writes outside Creator Engine asset directory.
- No publishing without approval.
- No Recordly/OpenScreen bridge enabled without explicit user toggle.

---

## 22. Implementation Roadmap

### Phase 0 — Repository alignment

Implementation agent should first inspect ChaseOS repo and answer:

- What is the current app framework?
- Where do modules live?
- Is there a database?
- Is there a file storage abstraction?
- Is there an agent/tool registry?
- Is Hermes already integrated?
- Is OpenClaw already integrated?
- Is there a Feature Manifest system?
- Is there an existing RAG/vector store?
- Is FFmpeg already available?
- Is Whisper already available?

Do not start coding until these are mapped.

### Phase 1 — MVP skeleton

Deliverables:

- `creator-engine` module folder
- types/models
- basic UI route/page
- job store
- file asset store
- provider interface
- manual provider
- Recordly provider with folder/file ingestion only

### Phase 2 — transcription

Deliverables:

- audio extraction
- Whisper provider abstraction
- transcript output JSON
- transcript review UI

### Phase 3 — script/caption/social generation

Deliverables:

- prompt templates
- AI generation services
- clean transcript
- voiceover script
- captions SRT/VTT
- social pack
- memory card

### Phase 4 — basic RAG

Deliverables:

- source registry
- document chunking
- embeddings storage
- local docs/brand memory retrieval
- RAG context pack

### Phase 5 — GitHub/repo RAG

Deliverables:

- GitHub README/docs/releases/issues/PR ingestion
- repo fact sheet generation
- source-aware script generation

### Phase 6 — FFmpeg preview rendering

Deliverables:

- caption burn-in preview
- voiceover muxing
- audio normalization
- export profiles

### Phase 7 — Hermes/OpenClaw tools

Deliverables:

- creator job tools exposed to Hermes
- OpenClaw skill wrapper or tool bridge
- approval workflow

### Phase 8 — Recordly bridge research/prototype

Deliverables:

- decide bridge architecture
- no unsafe UI automation
- implement minimal local bridge in separate branch/fork if needed
- test reading current session and applying captions/regions

### Phase 9 — OpenScreen MCP adapter

Deliverables:

- track OpenScreen MCP issue
- implement adapter if MCP lands
- otherwise fork/prototype minimal bridge based on OpenScreen proposal

---

## 23. Acceptance Criteria for MVP

The MVP is successful when:

1. User records a video with Recordly.
2. ChaseOS detects or imports the video.
3. User adds a context prompt or voice note.
4. ChaseOS creates a job.
5. ChaseOS extracts/transcribes audio.
6. ChaseOS creates a cleaned transcript.
7. ChaseOS creates a script.
8. ChaseOS creates captions.
9. ChaseOS creates a social pack.
10. ChaseOS creates a memory card.
11. User can review outputs.
12. Optional preview render works with captions/voiceover.
13. Hermes/OpenClaw can trigger and check the workflow through safe tools.

---

## 24. Key Engineering Warnings

### 24.1 Do not overbuild training first

Training is not needed for MVP.

Start with:

- prompting
- RAG
- structured outputs
- review gates
- saved examples

Training/fine-tuning can come later after ChaseOS has enough approved/rejected creator examples.

### 24.2 Do not assume OpenScreen MCP is available

OpenScreen MCP is currently a proposed feature, not an available integration.

### 24.3 Do not ignore Recordly AGPL

Recordly is AGPL 3.0. Treat direct code reuse carefully.

### 24.4 Do not make ChaseOS depend on one recorder

Use provider adapters so Recordly, OBS, OpenScreen, and manual upload can all work.

### 24.5 Do not publish without review

This should be a content engine, not an uncontrolled posting bot.

---

## 25. Recommended First Implementation Prompt for Claude Code / Codex

Use this after placing the file in the ChaseOS repo:

```text
Read docs/creator-engine/chase-os-creator-engine-spec.md fully.

Then inspect the ChaseOS repository structure and produce an implementation plan for Phase 0 and Phase 1 only.

Do not implement yet.

Your plan must identify:
- where the Creator Engine module should live
- what existing database/storage/tooling patterns ChaseOS already uses
- whether there is an existing agent/tool registry for Hermes/OpenClaw
- how to add the Recordly provider as file-ingestion only for MVP
- how to represent CreatorJob, TranscriptSegment, CaptionCue, EditPlan, and RagContextPack
- what files you would create/change
- what risks or missing dependencies exist

Keep Option 1 as the build target.
Keep Option 2 as roadmap only.
Do not include OpenHuman.
Do not assume OpenScreen MCP is implemented.
```

---

## 26. References

Sources used to prepare this spec:

1. Recordly repository: `https://github.com/webadderallorg/Recordly`
2. Recordly package file: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/package.json`
3. Recordly IPC handlers: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/handlers.ts`
4. Recordly recording handler: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/register/recording.ts`
5. Recordly export handler: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/register/export.ts`
6. Recordly captions handler: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/register/captions.ts`
7. Recordly caption generator: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/captions/generate.ts`
8. Recordly Whisper model helper: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/captions/whisper.ts`
9. Recordly project handler: `https://raw.githubusercontent.com/webadderallorg/Recordly/main/electron/ipc/register/project.ts`
10. Recordly extension API: `https://github.com/webadderallorg/Recordly/blob/main/EXTENSIONS.md`
11. OpenScreen repository: `https://github.com/siddharthvaddem/openscreen`
12. OpenScreen package file: `https://raw.githubusercontent.com/siddharthvaddem/openscreen/main/package.json`
13. OpenScreen IPC handlers: `https://raw.githubusercontent.com/siddharthvaddem/openscreen/main/electron/ipc/handlers.ts`
14. OpenScreen MCP feature request: `https://github.com/siddharthvaddem/openscreen/issues/574`
15. Hermes Agent repository: `https://github.com/nousresearch/hermes-agent`
16. Hermes Agent docs/site: `https://hermes-agent.nousresearch.com/`
17. OpenClaw repository: `https://github.com/openclaw/openclaw`
18. Model Context Protocol server concepts: `https://modelcontextprotocol.io/docs/learn/server-concepts`
19. GNU AGPL v3 license text: `https://www.gnu.org/licenses/agpl.txt`
20. OpenScreen MIT license: `https://github.com/siddharthvaddem/openscreen/blob/main/LICENSE`

---

## 27. Final Direction

Build this in ChaseOS as a **Creator Engine**, starting with Option 1.

The winning path is:

```text
Recordly recording
+ ChaseOS file ingestion
+ Whisper transcription
+ RAG context pack
+ script/caption/social generation
+ optional voiceover
+ FFmpeg preview render
+ human review
+ memory card
+ Hermes/OpenClaw tools
```

Then later:

```text
Recordly/OpenScreen local bridge or MCP
+ visual video understanding
+ timeline edit plan application
+ auto-shorts
+ performance learning
```

This keeps the workflow useful immediately while preserving the future agentic editing roadmap.
