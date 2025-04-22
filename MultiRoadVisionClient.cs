using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Collections;

public class MultiRoadVisionClient : MonoBehaviour
{
    [System.Serializable]
    public struct RoadFeed
    {
        public string roadID;
        public Camera cam;
        public RawImage outputDisplay;
    }

    public RoadFeed[] roads;
    public int captureWidth = 640;
    public int captureHeight = 480;
    public float captureInterval = 0.1f;
    public string serverURL = "http://127.0.0.1:5000/detect";

    void Start()
    {
        for (int i = 0; i < roads.Length; i++)
            StartCoroutine(SendVideoFrames(i));
    }

    IEnumerator SendVideoFrames(int idx)
    {
        var feed = roads[idx];
        while (true)
        {
            yield return SendFrame(feed);
            yield return new WaitForSeconds(captureInterval);
        }
    }

    IEnumerator SendFrame(RoadFeed feed)
    {
        var rt = new RenderTexture(captureWidth, captureHeight, 24);
        feed.cam.targetTexture = rt;
        feed.cam.Render();
        RenderTexture.active = rt;
        var tex = new Texture2D(captureWidth, captureHeight, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, captureWidth, captureHeight), 0, 0);
        tex.Apply();
        feed.cam.targetTexture = null;
        RenderTexture.active = null;
        Destroy(rt);

        byte[] jpg = tex.EncodeToJPG();
        Destroy(tex);

        // send image + roadID
        var form = new WWWForm();
        form.AddBinaryData("image", jpg, "frame.jpg", "image/jpeg");
        form.AddField("roadID", feed.roadID);

        using (var www = UnityWebRequest.Post(serverURL, form))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success)
            {
                var outTex = new Texture2D(2, 2);
                if (outTex.LoadImage(www.downloadHandler.data))
                    feed.outputDisplay.texture = outTex;
            }
            else
            {
                Debug.LogError($"[Road {feed.roadID}] {www.error}");
            }
        }
    }
}
