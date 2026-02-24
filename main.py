import os
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Dict
import logging

load_dotenv()

app = FastAPI(title="Sandesh AI Integration Service")

SANDESH_API_KEY = os.getenv("SANDESH_API_KEY")
SANDESH_CAMPAIGN_URL = "https://api.sandeshai.com/whatsapp/campaign/api/"

logging.basicConfig(level=logging.INFO)

if not SANDESH_API_KEY:
    raise Exception("SANDESH_API_KEY not set")

# --------- Webhook Model ---------
class WebhookPayload(BaseModel):
    whatsappNumber: str
    campaignName: str
    contactName: str
    Number: Optional[str] = None
    Name: Optional[str] = None
    budget: Optional[str] = None
    location: Optional[str] = None
    property: Optional[str] = None


@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload):
    logging.info(f"Received webhook: {payload}")

    # Clean phone number (use whatsappNumber first, fallback to Number)
    phone = payload.whatsappNumber
    name = payload.contactName 

    print(payload)

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number missing")

    # Prepare Sandesh campaign payload
    campaign_payload = {
        "apiKey": SANDESH_API_KEY,
        "campaignName": payload.campaignName,
        "whatsappNumber": payload.whatsappNumber,
        "contactName": name,
        "templateVariables": [payload.Number,payload.Name,payload.budget,payload.location,payload.property]  
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                SANDESH_CAMPAIGN_URL,
                json=campaign_payload
            )

        if response.status_code != 200:
            logging.error(response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail="Sandesh API error"
            )

        return {
            "status": "success",
            "sandesh_response": response.json()
        }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Sandesh API timeout")

    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 for production deployment (Docker/Cloud)
    uvicorn.run(app, host="0.0.0.0", port=8000)