# AI Agent Tools Guide

## Overview
Your AI assistant now has function calling capabilities! The AI can automatically call external APIs to fetch data during conversations.

**Language**: The AI speaks in **Bangla (Bengali)** to farmers.

## Currently Implemented Tools

### 1. `get_farmer_data`
- **Description**: Retrieves farmer information from the AgriSense API
- **Endpoint**: `POST https://agrisense-z6ks.onrender.com/api/voice/get-farmer-data`
- **Parameters**: `phone_number` (string)
- **Usage**: The AI will automatically call this when it needs farmer information

### 2. `get_market_prices`
- **Description**: Gets the latest market prices for crops (Corn, Mango, Rice, etc.)
- **Endpoint**: `GET https://agrisense-z6ks.onrender.com/api/prices/public`
- **Parameters**: None
- **Usage**: The AI calls this when farmers ask about current market prices
- **Sample Response**: `{"prices":[{"name":"Corn","unit":"mon","price":2800},{"name":"Mango","unit":"mon","price":2000}]}`

### 3. `add_product_to_selling_list`
- **Description**: Adds a product to the farmer's selling list
- **Endpoint**: `POST https://agrisense-z6ks.onrender.com/api/voice/add-product-by-phone`
- **Parameters**: 
  - `phone_number` (required): Farmer's phone with country code
  - `product_name` (required): Name of the product
  - `unit_price` (required): Price per unit
  - `unit` (required): Unit type - "kg", "mon", "quintal", or "ton"
  - `description` (optional): Product description (max 1000 chars)
- **Usage**: Farmer says "I want to sell rice at 1200 taka per mon"

### 4. `delete_product_from_selling_list`
- **Description**: Removes a product from farmer's selling list
- **Endpoint**: `POST https://agrisense-z6ks.onrender.com/api/voice/delete-product-by-phone`
- **Parameters**:
  - `phone_number` (required): Farmer's phone with country code
  - `product_id` (required): UUID of the product to delete
- **Usage**: Farmer says "Remove my rice listing" (AI gets product_id from farmer data first)

## How It Works

1. **Farmer calls** → AI answers in Bangla
2. **AI identifies need** for data based on conversation
3. **AI automatically calls** the appropriate tool
4. **Your API returns** the data
5. **AI speaks** the results to the farmer in Bangla

### Example Conversations (in Bangla):

**Checking Farmer Info:**
- Farmer: "আমার তথ্য দেখাও" (Show my information)
- AI: *calls `get_farmer_data`*
- AI: "আপনার নাম... আপনার ৫ একর জমিতে ধান এবং গম চাষ করা হয়েছে..."

**Checking Market Prices:**
- Farmer: "বাজারে ধানের দাম কত?" (What's the rice price in market?)
- AI: *calls `get_market_prices`*
- AI: "বর্তমানে ধানের দাম মন প্রতি ১২০০ টাকা..."

**Adding Product to Sell:**
- Farmer: "আমি ধান বিক্রি করতে চাই, মন প্রতি ১৫০০ টাকা" (I want to sell rice at 1500 taka per mon)
- AI: *calls `add_product_to_selling_list`*
- AI: "আপনার ধান বিক্রয় তালিকায় যুক্ত করা হয়েছে..."

**Deleting Product:**
- Farmer: "আমার আম বিক্রয় তালিকা থেকে সরিয়ে দাও" (Remove mango from my selling list)
- AI: *calls `get_farmer_data` first to get product_id, then `delete_product_from_selling_list`*
- AI: "আপনার আম বিক্রয় তালিকা থেকে সরানো হয়েছে..."

## Adding More Tools

### Step 1: Add Tool Definition

Edit `main.py` and add to the `TOOLS` list (around line 33):

```python
TOOLS = [
    {
        "type": "function",
        "name": "get_farmer_data",
        "description": "Retrieves detailed information about a farmer...",
        "parameters": {...}
    },
    # Add your new tool here
    {
        "type": "function",
        "name": "get_weather_forecast",  # Your tool name
        "description": "Gets 7-day weather forecast for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or region name"
                },
                "days": {
                    "type": "number",
                    "description": "Number of days to forecast (1-7)"
                }
            },
            "required": ["location"]
        }
    }
]
```

### Step 2: Add Tool Handler

In the `execute_tool` function (around line 69), add your handler:

```python
async def execute_tool(function_name: str, arguments: dict):
    """Execute the requested tool/function and return the result."""
    print(f"Executing tool: {function_name} with arguments: {arguments}")
    
    if function_name == "get_farmer_data":
        # ... existing code ...
    
    # Add your new tool handler
    elif function_name == "get_weather_forecast":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://your-weather-api.com/forecast",
                    params=arguments,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data}
                    else:
                        return {"success": False, "error": f"API error {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": f"Unknown function: {function_name}"}
```

### Step 3: Update System Message (Optional)

Update `SYSTEM_MESSAGE` (line 24) to inform the AI about new capabilities:

```python
SYSTEM_MESSAGE = (
    "You are a helpful AI assistant for farmers. You can help them with information about "
    "their farm, crops, weather, and agricultural needs. When a farmer calls, you can look up "
    "their information using their phone number and provide weather forecasts for their location. "
    "Always be polite, clear, and provide helpful agricultural advice."
)
```

## Example Tools You Can Add

1. **Weather Forecast**
   - Get weather predictions for farm planning

2. **Place Order**
   - Order seeds, fertilizer, equipment

3. **Check Inventory**
   - Check available stock of products

4. **Schedule Consultation**
   - Book appointments with agricultural experts

5. **Pest Information**
   - Get information about pest control

6. **Market Prices**
   - Check current market prices for crops

## Testing

### Test all tools (speak in Bangla):

1. Call your Twilio number or use `/make-call` endpoint
2. **Test `get_farmer_data`:**
   - "আমার তথ্য দেখাও" (Show my information)
   - "আমার ফসলের তথ্য কি?" (What are my crops?)
3. **Test `get_market_prices`:**
   - "বাজারে দাম কত?" (What are the market prices?)
   - "ধানের দাম জানাও" (Tell me rice price)
4. **Test `add_product_to_selling_list`:**
   - "আমি গম বিক্রি করতে চাই মন প্রতি ২৫০০ টাকায়" (I want to sell wheat at 2500 taka per mon)
   - "ধান যোগ করো ১৮০০ টাকা কেজি" (Add rice 1800 taka per kg)
5. **Test `delete_product_from_selling_list`:**
   - "আমার পণ্য মুছে দাও" (Delete my product)
   - Note: You'll need the product_id from your farmer data first

## Tool Response Format

Your API should return JSON. The AI will receive whatever you return from `execute_tool`:

**Success example:**
```json
{
  "success": true,
  "data": {
    "farmer_name": "John Doe",
    "farm_size": "5 acres",
    "crops": ["rice", "wheat"]
  }
}
```

**Error example:**
```json
{
  "success": false,
  "error": "Farmer not found"
}
```

## Debugging

Check your server logs for:
- `Executing tool: get_farmer_data with arguments: ...`
- `Tool result: {...}`
- `Function call detected: ...`

These logs show when tools are called and their results.

## Limits

- Maximum 128 tools per session
- Each tool call has a 10-second timeout
- The AI decides automatically when to use tools (based on conversation context)

## Tips

1. Write clear tool descriptions - the AI uses them to decide when to call
2. Keep parameter descriptions specific
3. Return structured, easy-to-speak data
4. Handle errors gracefully in your APIs
5. Test each tool individually before adding to production

