import time
import subprocess, json
import weaviate
import vertexai
import openai
from vertexai.preview.language_models import ChatModel, InputOutputTextPair
from vertexai.preview.language_models import TextGenerationModel
from vertexai.preview.language_models import TextEmbeddingModel


def text_embedding(data):
    """Text embedding with a Large Language Model."""
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
    embeddings = model.get_embeddings([data])
    for embedding in embeddings:
        vector = embedding.values
        return vector

# < ---- GOOGLE TEXT-BISON MODEL ---->
def text_predict_large_language_model_sample(
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    content: str,
    location: str = "us-central1",
    tuned_model_name: str = "",
    ):
    """Predict using a Large Language Model."""
    vertexai.init(project=project_id, location=location)
    model = TextGenerationModel.from_pretrained(model_name)
    if tuned_model_name:
        model = model.get_tuned_model(tuned_model_name)
    response = model.predict(
        content,
        temperature=temperature,
        max_output_tokens=max_decode_steps,
        top_k=top_k,
        top_p=top_p,)
    return response.text

# < ---- GOOGLE CHAT-BISON MODEL ---->
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

# < ---- OPEN=AI CHAT-BISON MODEL ---->
def answer_question_text_completion_endpoint(
    question,
    context,
    model="text-davinci-003", # chat gpt 3.5 turbo
    max_tokens=600,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """

    try:
        # Create a completions using the question and context
        response = openai.Completion.create(
            prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )
        print("response!", response)
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        return ""

def answer_question_chat_completion_endpoint(
    question,
    context,
):
    try:
        # Create a completions using the question and context
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "system", "content": "You are a customer success chatbot, and can only provide brief answers no longer than 500 words. Answer the question based on the following context, and if the question can't be answered based on the context, say \"I don't know, refer to the Harness Docs.\" Don't provide an answer that doesn't respond to the question. Don't make any information up, only use the context provided."},
        {"role": "assistant", "content": context},
        {"role": "user", "content": "use the context provided earlier to answer the question: " + question}
        ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(e)
        return ""


def main():
    # connect to Weaviate
    client = weaviate.Client(
    url = "http://34.132.65.16/", 
    )

    openai.api_key = "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"

    # <--- ENTER QUESTION HERE --->
    client_question = "Can you help me get rid of this error message “Execution reached limit for the day, please contact support.”"
    print("\nClient Question:", client_question)

    start_question_embedding = time.time()
    client_question_vector = text_embedding(client_question)
    end_question_embedding = time.time()

    nearVector = {
        "vector": client_question_vector
    }

    start_vector_fetch = time.time()
    # find nearest vectors in Weaviate
    result = client.query.get(
            "HarnessDocsTestWithNG", ["text", "url"]
        ).with_near_vector(
            nearVector
        ).with_limit(1).with_additional(['certainty']
        ).do()
    end_vector_fetch = time.time()
    weaviate_context = ""
    for item in result["data"]["Get"]["HarnessDocsTestWithNG"]:
        weaviate_context += item['text']

    # context = "You are a customer success chatbot, and can only provide brief answers no longer than 500 words. Answer the question based on the following context, and if the question can't be answered based on the context, say \"I don't know, refer to the Harness Docs.\" Don't provide an answer that doesn't respond to the question. Don't make any information up, only use the context provided.\n" + weaviate_context
    # context = "Use the provided context delimited by triple quotes to answer questions. If the answer cannot be found in the context, write \"I could not find an answer.\"\n" + "\"\"\"" + weaviate_context + "\"\"\""
    context = "You are a Harness Bot, a customer service chatbot for Harness. You only answer customer questions about Harness and its products. You only use the information provided below, and will not innovate anything. Do not respond with anything that is not explicitly in the text below. Don't use any knowledge that is your own. Only use the words and phrases from this context below. If the question can't be answered using the information below, just say \"I don't know\", and that's completely acceptable. Do not provide any references not mentioned below. At the end, only cite this link and no other links. Cite this link if the context does not explicitly mention the information: " + result["data"]["Get"]["HarnessDocsTestWithNG"][0]["url"] + "\nContext: \n" + weaviate_context
    # context = "You are a customer chatbot and are programmed to only respond to customer questions about Harness. If you do not know the answer, just cite this url: " + result["data"]["Get"]["HarnessDocsTestWithNG"][0]["url"][:-1] + ". Otherwise, respond in a succint yet descriptive manner. Make sure you only use the context provided below, and no outside knowledge. If the context doesn't include an answer to the question, just cite the url i provided earlier. \nContext:\n" + weaviate_context;
    # context = " The answer to this question is in the context below. Cite this URL at the end of your answer: " + result["data"]["Get"]["HarnessDocsTestWithNG"][0]["url"][:-1] +". Use the following context to answer this question: \n" + weaviate_context
    # context = " Act as if you are a customer chatbot for Harness. Use only the context below to answer your question.\nContext:\n" + weaviate_context
    prompt = client_question + "\n" + context

    start_response = time.time()

    # response = text_predict_large_language_model_sample("ml-play-351223", "text-bison@001", 0, 1024, 0.8, 40, prompt, "us-central1")
    # response = chat_predict_large_language_model_sample(client_question, context, "ml-play-351223", "chat-bison@001", 0, 1024, 0.8, 40, "us-central1")
    # response = answer_question_text_completion_endpoint(client_question, context)
    # response = answer_question_chat_completion_endpoint(client_question, context)
   
   # run subprocess for azure chatgpt3 model (fast api ref)
    # subprocess.run([
    # 'curl',
    # '-X', 'POST',
    # 'http://35.202.125.234/chat',
    # '-H', 'accept: application/json',
    # '-H', 'Authorization: Bearer [bearer token]',
    # '-H', 'Content-Type: application/json',
    # '-d', json.dumps ({
    # "message": "what is my name" + "hello",
    # "provider": "azureopenai",
    # "context": "",
    # "examples": [],
    # "model_name": "gpt3",
    # "model_parameters": {
    #     "temperature": 0,
    #     "max_output_tokens": 1024,
    #     "top_p": 0.95,
    #     "top_k": 40
    # }})])
    end_response = time.time()

    print("\nTime taken for vectorizing question:", str(round(end_question_embedding - start_question_embedding, 2)))
    print("Time taken for getting context:", str(round(end_vector_fetch - start_vector_fetch, 2)))
    print("Time taken for chat-bison response:", str(round(end_response - start_response, 2)))

    print("\nCertainty of Weaviate Context:", str(round(result["data"]["Get"]["HarnessDocsTestWithNG"][0]["_additional"]["certainty"], 2)))

    print("\nContext Reference from Weaviate:", result["data"]["Get"]["HarnessDocsTestWithNG"][0]["url"])
    print("\nResponse from Model:")
    print("\n========================================================================")
    # print(prompt)
if __name__ == "__main__":
    main()

# < --- NOTES --->
# 1. If we increase limit to > 1 for the weaviate vector search, the model does not return a response
# 2. Weaviate result also returns the certainty of each vector
# 3. Things we can play with to modify response: temperature, max tokens, top_p, top_k