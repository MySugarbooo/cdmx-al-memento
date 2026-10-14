"""El estudio musical es una herramienta autónoma, no una imagen decorativa."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"kisumi-studio"

class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(BASE/"index.html").read_text(encoding="utf-8")
        cls.css=(BASE/"studio.css").read_text(encoding="utf-8")
        cls.js=(BASE/"studio.js").read_text(encoding="utf-8")

    def test_app_is_complete_and_responsive(self):
        html=self.html
        for ident in ("visualizer","audio-file","lyrics-file","lyrics-text","lyric-lines",
                      "show-lyrics","tab-auto","speech-language","transcribe-btn","export-lrc",
                      "sync-start","sync-next","export-btn","download-video","stop-record"):
            with self.subTest(id=ident):
                self.assertIn('id="'+ident+'"',html)
        self.assertIn("KISUMI",html)
        self.assertIn('id="demo-btn"',html)
        self.assertIn("function makeDemoWav()",self.js)
        self.assertIn("new File([buffer]",self.js)
        self.assertIn("Amau Kisumi",html)
        self.assertIn("1280",html)
        self.assertIn("720",html)
        self.assertIn("studio.css?v=5",html)
        self.assertIn("studio.js?v=5",html)
        self.assertIn("page-transitions.js?v=1",html)
        self.assertIn("@media(max-width:640px)",self.css)
        self.assertIn("prefers-reduced-motion",self.css)

    def test_audio_canvas_and_recorded_video(self):
        js=self.js
        for fragment in ("createAnalyser()","createMediaElementSource(audio)",
                         "createMediaStreamDestination()","state.recDest.stream.getAudioTracks()",
                         "canvas.captureStream(targetFPS)","new MediaRecorder(all",
                         "new Blob(chunks","link.download='kisumi-neon-studio-'",
                         "audio.addEventListener('ended'","audio.currentTime=0",
                         "video/mp4","video/webm","requestAnimationFrame(frame)"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,js)

    def test_multilingual_recognition_and_timestamp_parsing(self):
        js=self.js
        for fragment in ("new Worker('./transcribe-worker.js?v=1'","worker.postMessage",
                         "setTranscribing(true)","stopTranscription(",
                         "decodeAudioData","16000","isIOS","transcriptionWorker.terminate()",
                         "function parseLyrics(",
                         "function parseTimestamp(","[...line.matchAll",
                         "lrcStamp","showRows()"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,js)
        for term in ("Español","Français","日本語","한국어","العربية","हिन्दी"):
            self.assertIn(term,self.html)

    def test_user_audio_kept_local_and_external_model_is_explicit(self):
        js=self.js
        self.assertIn("URL.createObjectURL(file)",js)
        self.assertIn("file.arrayBuffer()",js)
        self.assertNotIn("fetch('https://api.openai.com",js)
        self.assertNotIn("navigator.mediaDevices.getUserMedia",js)
        self.assertIn("No se pudo transcribir aquí",js)
        self.assertIn("voces cantadas",self.html.lower())
        self.assertIn("procesamiento",self.html.lower())
        self.assertIn("Subir archivo de audio",self.html)

    def test_worker_is_quantized_chunked_and_cancellable(self):
        worker=(BASE/"transcribe-worker.js").read_text(encoding="utf-8")
        for text in ("onnx-community/whisper-tiny", "dtype:'q8'",
                     "device:'wasm'","chunkSeconds=15","send('segment'",
                     "send('done'","send('error'"):
            self.assertIn(text,worker)

    def test_ios_crash_prevention_and_progress(self):
        for ident in ("cancel-transcribe","asr-ios-notice","ios-manual-btn"):
            self.assertIn('id="'+ident+'"',self.html)
        self.assertIn("if(isIOS)return;",self.js)
        self.assertIn("transcriptionWorker.terminate()",self.js)
        self.assertIn("Modo seguro para iPhone/iPad",self.js)
        self.assertIn("transcribir desde una computadora",self.html.lower())
        self.assertIn("Modo móvil",self.js)
        self.assertIn("function speechSamples(",self.js)
        self.assertIn("setTimeout(",self.js)
        self.assertIn("targetFPS=isCompact?24:30",self.js)
        self.assertIn("canvas.width=960;canvas.height=540",self.js)

if __name__=="__main__":
    unittest.main()
