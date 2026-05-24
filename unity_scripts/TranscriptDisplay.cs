using UnityEngine;
using TMPro;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class TranscriptDisplay : MonoBehaviour
{
    [Header("ROS Topics")]
    public string userTopicName = "/voice_command/text";
    public string assistantTopicName = "/voice_command/agent_text";

    [Header("UI References")]
    public TMP_Text userText;
    public TMP_Text assistantText;

    private ROSConnection ros;
    private string pendingUserText = null;
    private string pendingAssistantText = null;
    private readonly object lockObj = new object();

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<StringMsg>(userTopicName, OnUserTextReceived);
        ros.Subscribe<StringMsg>(assistantTopicName, OnAssistantTextReceived);

        if (userText != null) userText.text = "User: ";
        if (assistantText != null) assistantText.text = "Assistant: ";

        Debug.Log("TranscriptDisplay: Listening on " + userTopicName + " and " + assistantTopicName);
    }

    void Update()
    {
        lock (lockObj)
        {
            if (pendingUserText != null && userText != null)
            {
                userText.text = "User: " + pendingUserText;
                pendingUserText = null;
            }
            if (pendingAssistantText != null && assistantText != null)
            {
                assistantText.text = "Assistant: " + pendingAssistantText;
                pendingAssistantText = null;
            }
        }
    }

    void OnUserTextReceived(StringMsg msg)
    {
        lock (lockObj)
        {
            pendingUserText = msg.data;
        }
        Debug.Log("TranscriptDisplay: User -> " + msg.data);
    }

    void OnAssistantTextReceived(StringMsg msg)
    {
        lock (lockObj)
        {
            pendingAssistantText = msg.data;
        }
        Debug.Log("TranscriptDisplay: Assistant -> " + msg.data);
    }
}
