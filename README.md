# CS 4273 OCR
Nick Thompson
Kaden Cochran
Eric Chen

## Build and Deploy

### Local Deployment
- Create a google vision API key by following the documentation [here](https://cloud.google.com/vision/docs/setup)  
- Create a python environment and install required libraries from `requirements.txt`
- Add the `FLASK_APP` environmental variable and run the application locally with:
```bash
$ export FLASK_APP=ocr.py
$ flask run
```

### App Engine Deployment