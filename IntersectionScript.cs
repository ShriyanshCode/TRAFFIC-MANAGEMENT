using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class IntersectionScript : MonoBehaviour
{
    public List<GameObject> stops; // A=0,B=1,C=2,D=3
    private List<StopScript> stopScripts = new();
    private int index = 0;
    public float wait = 5f;
    private bool next = true;

    void Start()
    {
        foreach (var obj in stops)
        {
            var s = obj.GetComponent<StopScript>();
            s.SetStop(true);
            stopScripts.Add(s);
        }
    }

    void Update()
    {
        if (next) StartCoroutine(Cycle());
    }

    IEnumerator Cycle()
    {
        next = false;
        using (var www = UnityWebRequest.Get("http://127.0.0.1:5000/decide"))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success)
            {
                var dec = JsonUtility.FromJson<Decision>(www.downloadHandler.text);
                index = dec.next; wait = dec.wait;
            }
            else
            {
                index = (index + 1) % stops.Count;
            }
        }

        stopScripts[index].SetStop(false);
        yield return new WaitForSeconds(wait);
        while (stopScripts[index].priority > 0)
            yield return new WaitForSeconds(0.1f);

        stopScripts[index].SetStop(true);
        next = true;
    }

    [System.Serializable]
    private class Decision { public int next; public float wait; }
}
