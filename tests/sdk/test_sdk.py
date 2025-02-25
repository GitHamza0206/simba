from simba_sdk import SimbaClient

client = SimbaClient(api_url="http://localhost:8000", api_key="test")

print(client.ask("What is the capital of France?"))


print(client.as_retriever())
