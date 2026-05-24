using System;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class AudioSubscriber : MonoBehaviour
{
    [Header("ROS Settings")]
    public string topicName = "/audio/to_unity";

    [Header("Audio Settings")]
    public int sampleRate = 24000;

    private ROSConnection ros;
    private AudioSource audioSource;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<StringMsg>(topicName, OnAudioReceived);

        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }
        audioSource.playOnAwake = false;
        audioSource.loop = false;

        Debug.Log("AudioSubscriber: Listening on " + topicName + " at " + sampleRate + " Hz");
    }

    void OnAudioReceived(StringMsg msg)
    {
        try
        {
            byte[] pcm16 = Convert.FromBase64String(msg.data);
            int sampleCount = pcm16.Length / 2;
            float[] floatSamples = new float[sampleCount];

            for (int i = 0; i < sampleCount; i++)
            {
                short s = (short)(pcm16[i * 2] | (pcm16[i * 2 + 1] << 8));
                floatSamples[i] = s / 32768f;
            }

            AudioClip clip = AudioClip.Create("PersonaPlexResponse", sampleCount, 1, sampleRate, false);
            clip.SetData(floatSamples, 0);

            audioSource.clip = clip;
            audioSource.Play();

            float duration = (float)sampleCount / sampleRate;
            Debug.Log("AudioSubscriber: Playing " + sampleCount + " samples (" + duration.ToString("F2") + " sec)");
        }
        catch (Exception e)
        {
            Debug.LogError("AudioSubscriber: Error - " + e.Message);
        }
    }
}
