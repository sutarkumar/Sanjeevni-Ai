import fs from "fs";              // File system module (file create/save karne ke liye)
import edgeTTS from "edge-tts";  // Text-to-Speech library

async function main() {

  // Output file ka path (yaha audio save hoga)
  const outputPath = "./audios/test.mp3";

  //  Edge TTS se audio stream generate kar rahe hain
  const stream = await edgeTTS.stream({
    text: "Hello, I am your AI avatar. Nice to meet you.", //  Jo text bolwana hai
    voice: "en-US-AriaNeural", // Voice selection (Microsoft neural voice)
  });

  //  File stream create (audio ko file me likhne ke liye)
  const fileStream = fs.createWriteStream(outputPath);

  // Stream ko chunk by chunk read kar rahe hain
  for await (const chunk of stream) {

    // Sirf audio type ke chunks ko handle karenge
    if (chunk.type === "audio") {

      //  Audio data ko file me write kar do
      fileStream.write(chunk.data);
    }
  }

  // File writing complete
  fileStream.end();

  //  Console pe message show karo
  console.log("Audio saved:", outputPath);
}

//  Function run karo aur error handle karo
main().catch(console.error);
