using System;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class MicPublisher : MonoBehaviour
{
    [Header("ROS Settings")]
    public string topicName = "/audio/from_unity";

    [Header("Microphone Settings")]
    public int sampleRate = 24000;
    public int maxRecordSeconds = 10;
    public KeyCode pushToTalkKey = KeyCode.Space;

    private ROSConnection ros;
    private AudioClip recordingClip;
    private string deviceName;
    private bool isRecording = false;
    private int recordingStartSample = 0;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(topicName);

        if (Microphone.devices.Length == 0)
        {
            Debug.LogError("MicPublisher: No microphone device found.");
            return;
        }

        deviceName = Microphone.devices[0];
        Debug.Log("MicPublisher: Using mic device: " + deviceName);
        Debug.Log("MicPublisher: Hold " + pushToTalkKey + " to record, release to publish.");
    }

    void Update()
    {
        if (string.IsNullOrEmpty(deviceName)) return;

        if (Input.GetKeyDown(pushToTalkKey) && !isRecording)
        {
            StartRecording();
        }
        else if (Input.GetKeyUp(pushToTalkKey) && isRecording)
        {
            StopRecordingAndPublish();
        }
    }

    void StartRecording()
    {
        recordingClip = Microphone.Start(deviceName, false, maxRecordSeconds, sampleRate);
        recordingStartSample = 0;
        isRecording = true;
        Debug.Log("MicPublisher: Recording started.");
    }

    void StopRecordingAndPublish()
    {
        int endSample = Microphone.GetPosition(deviceName);
        Microphone.End(deviceName);
        isRecording = false;

        if (recordingClip == null || endSample <= 0)
        {
            Debug.LogWarning("MicPublisher: No samples captured.");
            return;
        }

        float[] floatSamples = new float[endSample];
        recordingClip.GetData(floatSamples, 0);

        byte[] pcm16 = new byte[floatSamples.Length * 2];
        for (int i = 0; i < floatSamples.Length; i++)
        {
            float clamped = Mathf.Clamp(floatSamples[i], -1f, 1f);
            short s = (short)(clamped * 32767f);
            pcm16[i * 2] = (byte)(s & 0xff);
            pcm16[i * 2 + 1] = (byte)((s >> 8) & 0xff);
        }

        string b64 = Convert.ToBase64String(pcm16);
        StringMsg msg = new StringMsg(b64);
        ros.Publish(topicName, msg);

        Debug.Log("MicPublisher: Published " + floatSamples.Length + " samples (" + pcm16.Length + " bytes PCM16, " + b64.Length + " chars b64) to " + topicName);
    }
}
