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
        self.assertIn("studio.css?v=2",html)
        self.assertIn("studio.js?v=2",html)
        self.assertIn("page-transitions.js?v=1",html)
        self.assertIn("@media(max-width:640px)",self.css)
        self.assertIn("prefers-reduced-motion",self.css)

    def test_audio_canvas_and_recorded_video(self):
        js=self.js
        for fragment in ("createAnalyser()","createMediaElementSource(audio)",
                         "createMediaStreamDestination()","state.recDest.stream.getAudioTracks()",
                         "canvas.captureStream(30)","new MediaRecorder(all",
                         "new Blob(chunks","link.download='kisumi-neon-studio-'",
                         "audio.addEventListener('ended'","audio.currentTime=0",
                         "video/mp4","video/webm","requestAnimationFrame(frame)"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,js)

    def test_multilingual_recognition_and_timestamp_parsing(self):
        js=self.js
        for fragment in ("onnx-community/whisper-tiny","@huggingface/transformers@",
                         "automatic-speech-recognition","return_timestamps:true",
                         "task:'transcribe'","device:'wasm'","chunk_length_s:30",
                         "decodeAudioData","16000","function parseLyrics(",
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
        self.assertIn("puede fallar con voces cantadas",self.html)
        self.assertIn("procesamiento",self.html.lower())
        self.assertIn("Subir archivo de audio",self.html)

if __name__=="__main__":
    unittest.main()
