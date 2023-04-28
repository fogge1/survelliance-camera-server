# Flask server camera
This the video processing part of our surveillance camera school project. It's a flask server that takes in a video feed from an ESP32 camera via Wi-Fi. It uses OpenCV for video processing, Vonage API for SMS notifications and Firebase for storing different IP addresses, from both the camera and the API itself. 

## Related GitHub repos
[API](https://github.com/fogge1/survelliance-camera-server)

[ESP32](https://github.com/fogge1/surveillance-camera-esp32)

[WEB](https://github.com/abbGusjak251/iot-surveillance-web-app)

## Installation
Clone project
```bash
pip install -r requirements.txt
```
## Usage

```bash
python camera-handler.py --ip 0.0.0.0 --port <port>
```
#### Endpoints
```
/available_cams
```
Returns a list of indexes of cameras available. These indexes are then used to specify the **camID**.

```
/video_feed/<int:camID>
```
Returns a feed of jpeg images for the **selected** camera.

## License
This project is licensed under the MIT License.
