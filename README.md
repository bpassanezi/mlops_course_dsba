# mlops_course_dsba
Repo for DSBA MLOps


## Docker

How to test docker file is working?

**1. Build the Image**
This command reads your Dockerfile and creates a packaged image named scoring-api.

'''bash
docker build -t scoring-api.
'''


**2. Run the Container**
Once the build is successful, run this to start the API. We map port 8000 on your machine to port 80 inside the container.

'''bash
docker run -d --name scoring-container -p 8000:80 scoring-api

'''

**3. Verify it's Working**
You can test the running container by sending a request from your terminal:

'''bash
curl -X POST http://127.0.0.1:8000/scoring/ \
     -H "Content-Type: application/json" \
     -d '{"address": "my_address", "surface": 100, "num_rooms": 3}'
'''

Useful Commands for later:
Check logs: docker logs scoring-container (useful if it crashes)
Stop it: docker stop scoring-container
Remove it: docker rm scoring-container