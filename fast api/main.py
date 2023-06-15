import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

import time
import subprocess, json
import ast

import weaviate
import vertexai
import openai

from vertexai.preview.language_models import ChatModel, InputOutputTextPair
from vertexai.preview.language_models import TextGenerationModel
from vertexai.preview.language_models import TextEmbeddingModel

app = FastAPI()

def chat_predict_large_language_model_sample(
    client_question: str,
    provided_context,
    project_id: str,
    model_name: str,
    temperature: float,
    max_output_tokens: int,
    top_p: float,
    top_k: int,
    location: str = "us-central1",
    ) :
    """Predict using a Large Language Model."""
    vertexai.init(project=project_id, location=location)

    chat_model = ChatModel.from_pretrained(model_name)
    parameters = {
      "temperature": temperature,
      "max_output_tokens": max_output_tokens,
      "top_p": top_p,
      "top_k": top_k,
    }
    chat = chat_model.start_chat(
        context = provided_context,
        examples=[
            InputOutputTextPair(
                input_text='How many moons does Mars have?',
                output_text='Since the context below has no information about this, I cannot answer this question. Please refer to the Harness Docs or contact Harness support.',
            ),
            InputOutputTextPair(
                input_text='What\'s the weather like?',
                output_text='Since the context below has no information about this, I cannot answer this question. Please refer to the Harness Docs or contact Harness support.',
            )
        ]
    ) 
    response=chat.send_message(client_question,**parameters)
    return response.text

def text_embedding(data):
    """Text embedding with a Large Language Model."""
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
    embeddings = model.get_embeddings([data])
    for embedding in embeddings:
        vector = embedding.values
        return vector

class ChatParameters(BaseModel):
    model: str
    question: str

@app.post("/chat")
def chat(chat_params: ChatParameters):
    client = weaviate.Client(
    url = "http://34.132.65.16/", 
    )
    

    client_question_vector = text_embedding(chat_params.question)

    nearVector = {
        "vector": client_question_vector
    }

    result = client.query.get(
            "HarnessDocsTestWithNG", ["text", "url"]
        ).with_near_vector(
            nearVector
        ).with_limit(1).with_additional(['certainty']
        ).do()
    
    weaviate_context = ""
    for item in result["data"]["Get"]["HarnessDocsTestWithNG"]:
        weaviate_context += item['text']

    prompt = "You are a Harness Bot, a customer service chatbot for Harness. You only answer customer questions about Harness and its products. You only use the information provided below, and will not innovate anything. Do not respond with anything that is not explicitly in the text below. Don't use any knowledge that is your own. Only use the words and phrases from this context below. If the question can't be answered using the information below, just say \"I don't know\", and that's completely acceptable. Do not provide any references not mentioned below. At the end, only cite this link and no other links. Cite this link if the context does not explicitly mention the information: " + result["data"]["Get"]["HarnessDocsTestWithNG"][0]["url"] + "\nContext: \n" + weaviate_context

    if chat_params.model == "chat-bison":
        response = chat_predict_large_language_model_sample(chat_params.question, prompt, "ml-play-351223", "chat-bison@001", 0, 1024, 0.8, 40, "us-central1")
        
        return response
    
    elif chat_params.model == "azuregpt3":
        response = subprocess.run([
        'curl',
        '-X', 'POST',
        'http://35.202.125.234/chat',
        '-H', 'accept: application/json',
        '-H', 'Authorization: Bearer [bearer token]',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps ({
        "message": chat_params.question + "\n" + prompt,
        "provider": "azureopenai",
        "context": "",
        "examples": [],
        "model_name": "gpt3",
        "model_parameters": {
            "temperature": 0,
            "max_output_tokens": 1024,
            "top_p": 0.95,
            "top_k": 40
        }})], capture_output=True).stdout.decode('utf-8')
        response = ast.literal_eval(response)

        return response["text"]
    
    else:
        return "Error in processing chat_model. Please enter either \'chat-bison\' or \'azuregpt3\'"