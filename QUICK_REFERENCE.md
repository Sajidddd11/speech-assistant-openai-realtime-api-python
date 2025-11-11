# Quick Reference Card - AI Farmer Assistant

## 🌾 Overview
AI voice assistant for Bangladeshi farmers - **speaks in Bangla (বাংলা)**

## 📞 How to Make a Call

**Postman/API:**
- **Method**: POST
- **URL**: `http://your-ngrok-url/make-call`
- **Body**:
```json
{
  "phone_number": "+8801788040850"
}
```

## 🛠️ Available Tools (4 Total)

| Tool | What It Does | When AI Uses It |
|------|--------------|-----------------|
| `get_farmer_data` | Get farmer profile & crops | "আমার তথ্য দেখাও" |
| `get_market_prices` | Get current crop prices | "বাজারে দাম কত?" |
| `add_product_to_selling_list` | Add product to sell | "ধান বিক্রি করতে চাই" |
| `delete_product_from_selling_list` | Remove product listing | "পণ্য মুছে দাও" |

## 💬 Test Phrases (in Bangla)

### Check Farmer Info:
- "আমার তথ্য দেখাও" (Show my information)
- "আমার ফসল কি?" (What are my crops?)

### Check Market Prices:
- "বাজারে ধানের দাম কত?" (What's rice price in market?)
- "আজকের বাজার দাম জানাও" (Tell me today's market prices)
- Responds with: Corn (2800/mon), Mango (2000/mon), Rice (1200/mon)

### Add Product to Sell:
- "আমি ধান বিক্রি করতে চাই মন প্রতি ১৫০০ টাকায়" 
  (I want to sell rice at 1500 taka per mon)
- "গম যোগ করো ২৫০০ টাকা মন" 
  (Add wheat 2500 taka per mon)

### Delete Product:
- "আমার ধান বিক্রয় তালিকা থেকে সরিয়ে দাও" 
  (Remove rice from my selling list)

## 🔗 API Endpoints

| Tool | Method | Endpoint |
|------|--------|----------|
| Get Farmer Data | POST | `https://agrisense-z6ks.onrender.com/api/voice/get-farmer-data` |
| Get Prices | GET | `https://agrisense-z6ks.onrender.com/api/prices/public` |
| Add Product | POST | `https://agrisense-z6ks.onrender.com/api/voice/add-product-by-phone` |
| Delete Product | POST | `https://agrisense-z6ks.onrender.com/api/voice/delete-product-by-phone` |

## 📝 Parameters Quick Reference

### Add Product Parameters:
```json
{
  "phone_number": "+8801788040850",
  "product_name": "Rice",
  "unit_price": 1500,
  "unit": "mon",  // Options: "kg", "mon", "quintal", "ton"
  "description": "High quality rice" // Optional
}
```

### Delete Product Parameters:
```json
{
  "phone_number": "+8801788040850",
  "product_id": "uuid-here"
}
```

## 🚀 Quick Start

1. **Start server:**
   ```bash
   python main.py
   ```

2. **Expose with ngrok:**
   ```bash
   ngrok http 5050
   ```

3. **Make a call:**
   ```bash
   curl -X POST https://your-ngrok.ngrok.io/make-call \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+8801788040850"}'
   ```

4. **Talk in Bangla!**

## 📊 Expected Behavior

1. ✅ AI answers in Bangla
2. ✅ Farmer asks question in Bangla
3. ✅ AI automatically detects which tool to use
4. ✅ AI calls your API
5. ✅ AI speaks results back in Bangla
6. ✅ Conversation continues naturally

## 🐛 Debugging

**Check server logs for:**
```
Executing tool: get_market_prices with arguments: {}
Tool result: {"success": True, "data": {...}}
Function call detected: ...
```

## 📌 Important Notes

- ⚠️ **Twilio Trial**: Only verified numbers work
- 🌍 **Enable Bangladesh** in Twilio geographic permissions
- 🗣️ **Language**: AI speaks in Bangla automatically
- ⏱️ **Timeout**: Each API call has 10 second timeout
- 🔧 **Max Tools**: Can add up to 128 tools total

## 💡 Adding More Tools

See `TOOLS_GUIDE.md` for detailed instructions on adding:
- Weather forecasts
- Pest information
- Equipment orders
- Expert consultations
- And more!

## 📞 Support URLs

- Twilio Console: https://console.twilio.com
- Verify Phone Numbers: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
- Geographic Permissions: https://console.twilio.com/us1/develop/voice/settings/geo-permissions
- Call Logs: https://console.twilio.com/us1/monitor/logs/calls

---

**Market Prices Reference** (from API):
```json
{
  "prices": [
    {"name": "Corn", "unit": "mon", "price": 2800},
    {"name": "Mango", "unit": "mon", "price": 2000},
    {"name": "Rice", "unit": "mon", "price": 1200}
  ]
}
```

