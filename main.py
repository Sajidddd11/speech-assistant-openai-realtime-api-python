import os
import json
import base64
import asyncio
import websockets
import aiohttp
from typing import Optional
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from twilio.rest import Client
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
PORT = int(os.getenv('PORT', 5050))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.8))
SYSTEM_MESSAGE = (
    "You are a helpful AI assistant for farmers in Bangladesh. You MUST speak in Bangla (Bengali) language. "
    "You can help farmers with: checking their farm information, viewing market prices for crops, "
    "adding products to their selling list, and removing products from their list. "
    "When a farmer calls, you can look up their information using their phone number. "
    "Always be polite, clear, and provide helpful agricultural advice in Bangla. "
    "Use simple Bangla words that farmers can easily understand. Speak in a friendly and supportive tone."
)
VOICE = 'alloy'

# Tool definitions - Add more tools here as needed
TOOLS = [
    {
        "type": "function",
        "name": "get_farmer_data",
        "description": "Retrieves detailed information about a farmer including their name, farm details, crops, and contact information using their phone number.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "The farmer's phone number in international format (e.g., +8801788040850)"
                }
            },
            "required": ["phone_number"]
        }
    },
    {
        "type": "function",
        "name": "get_market_prices",
        "description": "Gets the latest market prices for crops including corn, mango, rice, and other agricultural products. Returns current market rates.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "add_product_to_selling_list",
        "description": "Adds a new product to the farmer's selling list with product name, unit price, and unit type (kg, mon, quintal, ton).",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Farmer's phone number with country code (e.g., +8801788040850)"
                },
                "product_name": {
                    "type": "string",
                    "description": "Name of the product to sell (e.g., rice, wheat, corn)"
                },
                "unit_price": {
                    "type": "number",
                    "description": "Price per unit (must be non-negative)"
                },
                "unit": {
                    "type": "string",
                    "description": "Unit of measurement",
                    "enum": ["kg", "mon", "quintal", "ton"]
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the product (max 1000 characters)"
                }
            },
            "required": ["phone_number", "product_name", "unit_price", "unit"]
        }
    },
    {
        "type": "function",
        "name": "delete_product_from_selling_list",
        "description": "Removes a product from the farmer's selling list using the product ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Farmer's phone number with country code (e.g., +8801788040850)"
                },
                "product_id": {
                    "type": "string",
                    "description": "The UUID of the product to delete"
                }
            },
            "required": ["phone_number", "product_id"]
        }
    }
]
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'session.updated', 'response.function_call_arguments.done'
]
SHOW_TIMING_MATH = False

app = FastAPI()

# Pydantic model for outbound call request
class OutboundCallRequest(BaseModel):
    phone_number: str
    reason: Optional[str] = None

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

# Tool execution function
async def execute_tool(function_name: str, arguments: dict):
    """Execute the requested tool/function and return the result."""
    print(f"Executing tool: {function_name} with arguments: {arguments}")
    
    if function_name == "get_farmer_data":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://agrisense-z6ks.onrender.com/api/voice/get-farmer-data",
                    json=arguments,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"API returned status {response.status}: {error_text}"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif function_name == "get_market_prices":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://agrisense-z6ks.onrender.com/api/prices/public",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"API returned status {response.status}: {error_text}"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif function_name == "add_product_to_selling_list":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://agrisense-z6ks.onrender.com/api/voice/add-product-by-phone",
                    json=arguments,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "message": "Product added successfully"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"API returned status {response.status}: {error_text}"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif function_name == "delete_product_from_selling_list":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://agrisense-z6ks.onrender.com/api/voice/delete-product-by-phone",
                    json=arguments,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "message": "Product deleted successfully"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"API returned status {response.status}: {error_text}"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": f"Unknown function: {function_name}"}

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.post("/make-call")
async def make_outbound_call(request: Request, call_request: OutboundCallRequest):
    """Initiate an outbound call to the specified phone number."""
    try:
        # Validate Twilio credentials
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Twilio credentials not configured. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env file."
                }
            )
        
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Get the host from the request to build the callback URL
        host = request.url.hostname
        scheme = request.url.scheme
        port = request.url.port
        
        # Build the base URL
        if port and port not in [80, 443]:
            base_url = f"{scheme}://{host}:{port}"
        else:
            base_url = f"{scheme}://{host}"
        
        query_params = {}
        if call_request.reason:
            sanitized_reason = call_request.reason.strip()
            if sanitized_reason:
                query_params["reason"] = sanitized_reason[:250]

        call_url = f"{base_url}/incoming-call"
        if query_params:
            call_url = f"{call_url}?{urlencode(query_params)}"

        # Make the outbound call
        call = client.calls.create(
            to=call_request.phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=call_url
        )
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Call initiated to {call_request.phone_number}",
                "call_sid": call.sid
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    call_reason = request.query_params.get('reason')
    if call_reason:
        call_reason = call_reason[:250]

    # <Say> punctuation to improve text-to-speech flow
    response.say(
        "Please wait while we connect your call to the A. I. voice assistant, powered by Twilio and the Open A I Realtime API",
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
    response.pause(length=1)
    response.say(   
        "O.K. you can start talking!",
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
    host = request.url.hostname
    connect = Connect()
    stream = Stream(url=f'wss://{host}/media-stream')
    if call_reason:
        stream.parameter(name="reason", value=call_reason)
    connect.append(stream)
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model=gpt-realtime&temperature={TEMPERATURE}",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        call_reason = None
        reason_applied = False

        async def apply_call_reason(reason_value: str):
            nonlocal call_reason, reason_applied
            if reason_applied:
                return

            sanitized_reason = (reason_value or "").strip()
            if not sanitized_reason:
                return

            reason_applied = True
            call_reason = sanitized_reason[:250]

            combined_instructions = (
                f"{SYSTEM_MESSAGE}\n\n"
                f"The farmer is being contacted for the following reason: {call_reason}. "
                "Begin by greeting them warmly in Bangla and clearly stating this reason before offering additional help."
            )

            session_update_event = {
                "type": "session.update",
                "session": {
                    "instructions": combined_instructions
                }
            }
            await openai_ws.send(json.dumps(session_update_event))

            reason_message_event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"Call reason: {call_reason}. Greet the farmer in Bangla and clearly explain this reason before offering more help."
                            )
                        }
                    ]
                }
            }
            await openai_ws.send(json.dumps(reason_message_event))
            await openai_ws.send(json.dumps({"type": "response.create"}))
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                        params = data['start'].get('customParameters', {})
                        if isinstance(params, dict):
                            potential_reason = params.get('reason')
                            if potential_reason:
                                await apply_call_reason(potential_reason)
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.state.name == 'OPEN':
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    # Handle function calls
                    if response.get('type') == 'response.function_call_arguments.done':
                        print(f"Function call detected: {response}")
                        function_name = response.get('name')
                        call_id = response.get('call_id')
                        try:
                            arguments = json.loads(response.get('arguments', '{}'))
                        except json.JSONDecodeError:
                            arguments = {}
                        
                        # Execute the tool
                        result = await execute_tool(function_name, arguments)
                        print(f"Tool result: {result}")
                        
                        # Send the result back to OpenAI
                        function_output_event = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": json.dumps(result)
                            }
                        }
                        await openai_ws.send(json.dumps(function_output_event))
                        
                        # Trigger a new response from the assistant
                        await openai_ws.send(json.dumps({"type": "response.create"}))

                    if response.get('type') == 'response.output_audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)


                        if response.get("item_id") and response["item_id"] != last_assistant_item:
                            response_start_timestamp_twilio = latest_media_timestamp
                            last_assistant_item = response["item_id"]
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        await send_mark(websocket, stream_sid)

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Greet the user with 'Hello there! I am an AI voice assistant powered by Twilio and the OpenAI Realtime API. You can ask me for facts, jokes, or anything you can imagine. How can I help you?'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": "gpt-realtime",
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "turn_detection": {"type": "server_vad"}
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": VOICE
                }
            },
            "instructions": SYSTEM_MESSAGE,
            "tools": TOOLS,
            "tool_choice": "auto"
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Uncomment the next line to have the AI speak first
    # await send_initial_conversation_item(openai_ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
