export function startVoice() {
  const recognition = new window.webkitSpeechRecognition();
  recognition.continuous = true;

  recognition.onresult = (event) => {
    const text = event.results[event.results.length - 1][0].transcript;

    fetch("/api/voice_text", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({text})
    });
  };

  recognition.start();
}
