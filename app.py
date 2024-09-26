import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os
from twilio.rest import Client
import json
from customgpt_client import CustomGPT

load_dotenv()
project_id = os.getenv("project_id")
CustomGPT.api_key = os.getenv("api_key")
CustomGPT.base_url = os.getenv("base_url")

app = Flask(__name__)

# Load conversations from JSON
def load_conversations(file_path='conversations.json'):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save updated conversations to JSON
def save_conversations(conversations, file_path='conversations.json'):
    with open(file_path, 'w') as file:
        json.dump(conversations, file, indent=4)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    try:
        incoming_que = request.values.get('Body', '')
        fromNumber = request.values.get('From', '')
        print("Question: ", incoming_que)
        print("From: ", fromNumber)
        
        # Check if the number exists and fetch or create a conversation
        result = customGPTResponse(incoming_que, fromNumber)
        
        print("BOT Answer: ", result)
        SendTwilioSMS(result, fromNumber)
    except Exception as e:
        print(e)
        pass
    return jsonify({
        'fulfillmentText': 'Something went wrong'
    })

def customGPTResponse(input, fromNumber):
    try:
        conversations = load_conversations()

        # Check if the phone number already has a session ID
        if fromNumber in conversations:
            session_id = conversations[fromNumber]['session_id']
            print(f"Using existing session ID: {session_id}")
        else:
            # Create a new conversation if the number does not exist
            create_conversation = CustomGPT.Conversation.create(project_id=project_id, name='DialogFlow')
            conversation_data = create_conversation.parsed.data
            session_id = conversation_data.session_id
            # Store the new session ID
            conversations[fromNumber] = {'session_id': session_id}
            save_conversations(conversations)
            print(f"New session ID created: {session_id}")

        # Send the prompt and get the response
        response = CustomGPT.Conversation.send(project_id=project_id, session_id=session_id, prompt=input)
        response_customgpt = response.parsed.data
        openai_response = response_customgpt.openai_response

        print("PROMPT--->", input)
        print("RESPONSE", openai_response)
        return openai_response
    except Exception as e:
        print(e)

def SendTwilioSMS(result, number):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=result,
        from_='+18444860556',
        to=number  # Use the correct 'fromNumber' variable here
    )

    print(message.sid)
    return message

if __name__ == '__main__':
    app.run(debug=True)
 