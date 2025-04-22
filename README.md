# TRAFFIC-MANAGEMENT
BCSE417L Traffic Management System using Python, Unity

## IntersectionScript.cs:
Controls traffic light states and flow logic at the Unity intersection simulation.

## MultiRoadVisionClient.cs:
Connects Unity to the Flask backend, fetching vision-based vehicle data for each road.

## StopScript.cs:
Handles the stop/wait behavior of vehicles based on signal states in the Unity simulation.

## bbox_areas.txt:
Contains pre-defined bounding box regions for tracking vehicles on each road.

## mv1.ipynb:
Performs optical flow and YOLO-based vehicle motion analysis for live traffic footage.

## result1.ipynb:
Visualizes and evaluates traffic congestion data and detection results from processed videos.

## serv_cvrr.py:
Flask server that processes video frames, classifies traffic congestion, and serves control decisions.
