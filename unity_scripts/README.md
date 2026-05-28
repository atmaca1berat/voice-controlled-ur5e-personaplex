# Unity Scripts

Bu klasör Unity operatör arayüzünün production C# script'lerini içerir. Windows PC üzerinde Unity 2022.3 ile çalıştırılır ve interim raporda Section 3.5'te belgelenen operatör arayüzünü uygular.

## İçerik

- `MicPublisher.cs` — Push-to-talk (Space) mikrofon kaydı, 24 kHz mono PCM16, `/audio/from_unity` topic'ine base64 olarak yayınlar.
- `AudioSubscriber.cs` — `/audio/to_unity` topic'inden gelen base64 PCM16 sesi `AudioSource` üzerinden çalar.
- `TranscriptDisplay.cs` — `/voice_command/text` ve `/voice_command/agent_text` topic'lerini TextMeshPro UI alanlarına yazar.

## Bağımlılıklar

- Unity 2022.3.6f1
- ROS-TCP-Connector (`Unity.Robotics.ROSTCPConnector`)
- TextMeshPro
- `RosMessageTypes.Std` (std_msgs/String)

## Kullanım (Unity Editor)

1. Boş bir GameObject oluştur, üç script'i ekle.
2. `MicPublisher`: varsayılan tuş `Space`, varsayılan topic `/audio/from_unity`.
3. `AudioSubscriber`: `audioSource` alanına bir `AudioSource` ata (atanmazsa otomatik eklenir).
4. `TranscriptDisplay`: `userText` ve `assistantText` alanlarına TextMeshPro UI nesnelerini ata.
5. ROS Settings: WSL2 IP'sini ve port 10000'i tanımla (Window → Robotics → ROS Settings).

## Davranış

Bu script'ler push-to-talk ses yakalama, agent sesli yanıtın oynatılması ve kullanıcı/asistan transkriptlerinin TextMeshPro ile gösterilmesini sağlar. ROS 2 köprüsü ile haberleşme `std_msgs/String` mesajları üzerinden base64 kodlanmış PCM16 ses ile yapılır.
