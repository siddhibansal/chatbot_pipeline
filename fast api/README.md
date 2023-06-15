# ml-infra
All ML related infrastructure managed by the platform team at Harness.


# How to run

## Local run

One should have Python3.8+ installed on their machine to run this.

1. Run pip install -r requirements.txt to install all requirements
2. Run `source .env; uvicorn main:app --reload` on terminal
    * Depending on your shell, you may need to export the environment variables
3. Open http://127.0.0.1:8000/docs to play with input requests

### How to authorize for local requests

* Use "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJTVE8iLCJuYW1lIjoiSm9obiBEb2UiLCJpYXQiOjE1MTYyMzkwMjJ9.jfxeZZa8svIRisRy9NhcKeCWE6QXh3Cj0ksarw8kZlI" bearer token in the post requests.
  * This token is generated from https://jwt.io/ with "sub" value set to "LOG_SVC" the payload and "This is a secret" being the secret key.
* **Only acceptable values of "sub" are ["STO", "LOG_SVC", "CCM"]**


## Docker

TODO: Figure out vertex ai authentication while running from docker

To run this service in a container:

```
docker build -t ml-infra .
docker run -d --name genai-common-service -p 80:80 ml-infra
```

# Sample requests

## Vertex AI Chat endpoint

```json
curl -X 'POST' \
  'http://127.0.0.1:8000/chat' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJTVE8iLCJuYW1lIjoiSm9obiBEb2UiLCJpYXQiOjE1MTYyMzkwMjJ9.jfxeZZa8svIRisRy9NhcKeCWE6QXh3Cj0ksarw8kZlI' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "How many ways one can deploy a harness pipeline? Please only reply from the context that I provide and keep your answer very short",
  "provider": "vertexai",
  "context": "Harness is a great CI / CD tools. There are more than 5 ways to deploy a pipeline. Its CI module is the best in the world",
  "examples": [
    {
      "input": "Which is the best CI module in the world",
      "output": "Harness"
    }
  ],
  "model_name": "chat-bison",
  "model_parameters": {
    "temperature": 0,
    "max_output_tokens": 1024,
    "top_p": 0.95,
    "top_k": 40
  }
}'
```

## Azure ChatGPT endpoint

```json
curl -X 'POST' \
  'http://127.0.0.1:8000/chat' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJTVE8iLCJuYW1lIjoiSm9obiBEb2UiLCJpYXQiOjE1MTYyMzkwMjJ9.jfxeZZa8svIRisRy9NhcKeCWE6QXh3Cj0ksarw8kZlI' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "How many ways one can deploy a harness pipeline? Please only reply from the context that I provide and keep your answer very short",
  "provider": "azureopenai",
  "context": "Harness is a great CI / CD tools. There are more than 5 ways to deploy a pipeline. Its CI module is the best in the world",
  "examples": [
    {
      "input": "Which is the best CI module in the world",
      "output": "Harness"
    }
  ],
  "model_name": "gpt3",
  "model_parameters": {
    "temperature": 0,
    "max_output_tokens": 1024,
    "top_p": 0.95,
    "top_k": 40
  }
}'
```