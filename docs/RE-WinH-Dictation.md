# Reverse Engineering: Windows "Win+H" Voice Typing / Dictation

Source of truth: static RE of `C:\Windows\System32\DictationManager.dll`
(sha256 `60d2ee17625092e9f08c38b7aa3ab9425e4e0af99eed5f1839017f95253f227c`, x86_64 PE)
and discovery of host `C:\Windows\SystemApps\MicrosoftWindows.Client.CBS_cw5n1h2txyewy\TextInputHost.exe`.
Evidence collected via REA (Ghidra provider) string + symbol inventory.

## What Win+H actually is
- `Win+H` is a shell hotkey (handled by the shell / TextInputHost) that launches the
  **Voice Typing** panel. The actual dictation engine lives in `DictationManager.dll`,
  namespace `Dictation::DictationManager`.
- Source tree path embedded in symbols:
  `onecoreuap\shell\uxplat\speech\product\ux\dictationmanager\lib\...`

## Engine (the important part — it's a PUBLIC API)
`DictationManager` is a thin orchestration layer on top of the public WinRT Speech stack:
- `Windows.Media.SpeechRecognition.SpeechRecognizer` — the recognizer.
- `Windows.Media.SpeechRecognition.SpeechRecognitionTopicConstraint` — free-form
  **dictation** constraint (this is what makes it continuous natural-language dictation
  rather than command grammar).
- `Windows.Internal.SpeechRecognition.SystemSpeechRecognizerFactory` — builds the
  **on-device** system recognizer (no cloud endpoint strings were found; recognition is local).
- `Windows.Globalization.Language` — selects recognition language; language status is
  checked (LanguageAvailable / LanguageNotInstalled / TopicLanguageNotSupported).
- `SpeechRecognitionGrammarFileConstraint` — used only for the command/spelling sub-mode
  (`SpellingRecognitionProvider`), not for free dictation.

## Recognition flow (from symbol/state-machine evidence)
1. `InitializeRecognizer` — create `SpeechRecognizer`, set language, add
   `SpeechRecognitionTopicConstraint` (dictation), compile constraints.
2. `StartRecognition` -> `ContinuousRecognitionSession.StartAsync` (continuous mode).
3. Events consumed:
   - `HypothesisAvailable` -> partial text ("Hypothesis: %ws") shown live in the panel.
   - Segmentation / `ResultAvailable` -> finalized text segment -> `SetViewText` -> injected.
   - `StateChanged` -> drives an internal state machine with timeouts
     (StartingRecognitionTimeout, RecognitionTimeout, StoppingRecognitionTimeout, OnIdle).
4. `Stop/Cancel` -> `StopAsync` / `CancelAsync`, safe teardown.
- Telemetry activities confirm the pipeline: `SpeechRecognitionProviderStartActivity`,
  `...HypothesisAvailableActivity`, `...ResultAvailableActivity`, `...RecoCompletedActivity`,
  `...SegmentationEventActivity`, `...StopAsyncActivity`.

## Microphone & privacy
- Honors Windows mic privacy (`MicrophoneUnavailable`, `MicrophoneAccessNotAccepted`,
  "Dictation cannot access Microphone"). Must respect the OS microphone capability.

## Text injection into the focused field
- Final recognized segments are injected into whatever control has focus using the
  **Text Services Framework (TSF)** / input-injection path
  (`System\RemoteDictationInput`, `Input\Injection.AlpcPort\Server`). Win+H does NOT just
  send keystrokes; it uses TSF so it works in rich edit controls.

## Reproducibility conclusion (drives Aurora design)
The entire free-dictation experience is reproducible with **public** APIs:
- STT engine: `Windows.Media.SpeechRecognition.SpeechRecognizer` + `TopicConstraint`
  (continuous session, on-device, same engine Win+H uses). Reachable from Python via
  `winrt` / `winsdk` (Windows SDK projections).
- Live partial text: `HypothesisAvailable`; committed text: `ResultGenerated`.
- Hotkey: register a global hotkey (Aurora's "H + Win"-style trigger) to toggle listening.
- Text output: inject committed text into the focused field. MVP can use SendInput/Unicode
  typing; a later version can use a TSF text service for parity with Win+H.
- Language: select via `Windows.Globalization.Language`; must be installed on the system.

## Non-goals / caveats
- We do not reuse Microsoft binaries or private `Windows.Internal.*` factories; we rebuild
  equivalent behavior on the public `Windows.Media.SpeechRecognition` surface.
- Full TSF injection parity is a stretch goal; MVP uses SendInput Unicode injection.
