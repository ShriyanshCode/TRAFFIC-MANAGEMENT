using System.Collections.Generic;
using UnityEngine;

public class StopScript : MonoBehaviour
{
    public bool stop = true;
    public int priority => cars.Count;
    private HashSet<CarAIController> cars = new();

    private void OnTriggerEnter(Collider other)
    {
        if (other.TryGetComponent<CarAIController>(out var car))
            cars.Add(car);
    }

    private void OnTriggerExit(Collider other)
    {
        if (other.TryGetComponent<CarAIController>(out var car))
            cars.Remove(car);
    }

    void Update()
    {
        foreach (var c in cars)
        {
            if (stop)
            {
                c.SetSpeed(0);
                c.CheckPointSearch = false;
            }
            else
            {
                c.SetSpeed(c.speedLimit);
                c.CheckPointSearch = true;
            }
        }
    }

    public void SetStop(bool s) => stop = s;
}
