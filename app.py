# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse, HTMLResponse
# from llm import FAISS, DataBase, LLM
# from contextlib import asynccontextmanager
# from pathlib import Path
# import os
# from dotenv import load_dotenv
# import uvicorn
# from pydantic import BaseModel
# from jira_data_loader import load_data_from_jira
# from fastapi.middleware.cors import CORSMiddleware
# import signal
# import markdown2
# import bleach  # Add this import



# defects_llm = {}
# cleanup_done = False
# valid_defect_ids = set()  # Will be populated during startup

# def cleanup_resources():
#     global cleanup_done
#     if not cleanup_done:
#         if defects_llm:
#             defects_llm.clear()
#         cleanup_done = True

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     try:
#         BASE_DIR = Path(__file__).absolute().parent
#         ENV_PATH = os.path.join(BASE_DIR, ".env")
#         load_dotenv(ENV_PATH)
#         load_data_from_jira()
        
#         vs = FAISS.initialize()
#         db = DataBase()
#         faiss_data = vs.add_documents(db)
#         defects_llm.update(faiss_data)
        
#         # Get valid defect IDs from database
#         global valid_defect_ids
#         valid_defect_ids = {d['bug_id'] for d in db.defect_data}
#         print(f"Loaded valid defect IDs: {valid_defect_ids}")
        
#         yield
#     except Exception as e:
#         print(f"Error during startup: {e}")
#         cleanup_resources()
#         raise
#     finally:
#         cleanup_resources()

# def handle_exit(signum, frame):
#     cleanup_resources()
#     raise KeyboardInterrupt()

# signal.signal(signal.SIGINT, handle_exit)
# signal.signal(signal.SIGTERM, handle_exit)

# app  = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"], 
#     allow_headers=["*"],
# )

# class ChatRequest(BaseModel):
#     prompt: str
#     conversation_id: str = None

# @app.post("/defects/response")
# async def defects_response(chat_request: ChatRequest):
#     llm = LLM()
#     query = chat_request.prompt.lower()
#     db = DataBase()
    
#     # Check if query mentions invalid defect IDs using dynamic set
#     mentioned_ids = set([word.upper() for word in query.split() if word.upper().startswith('SCRUM-')])
#     invalid_ids = mentioned_ids - valid_defect_ids
    
#     if invalid_ids:
#         return JSONResponse(content={
#             "response": {
#                 "message": f"""**Invalid Defect IDs**

# The following defect IDs are not in the current database:
# - {', '.join(invalid_ids)}

# **Currently Active Defects:**
# - {', '.join(sorted(valid_defect_ids))}

# ---
# **Summary:**
# Please check the list of active defects above and try your query with a valid defect ID.""",
#                 "content_type": "markdown"
#             }
#         })

#     vs = FAISS.initialize()
#     vs.defect_embeddings = defects_llm["index"]
    
#     # Initialize relevant_defects with all defects as default
#     relevant_defects = db.defect_data

#     # Special handling for root cause and solution queries
#     if any(keyword in query for keyword in ['root', 'cause', 'why', 'solution', 'fix', 'resolve']):
#         mentioned_ids = [word.upper() for word in query.split() if word.upper().startswith('SCRUM-')]
#         if mentioned_ids and mentioned_ids[0] in valid_defect_ids:
#             # Get the specific defect directly from database
#             relevant_defects = [d for d in db.defect_data if d['bug_id'] == mentioned_ids[0]]
#             # Add debug logging
#             print(f"Found defect details: {relevant_defects[0] if relevant_defects else 'Not found'}")
#     elif not any(keyword in query for keyword in ['owner', 'who', 'list', 'all defect']):
#         # For specific queries that aren't about listing all defects
#         relevant_indices_scores = vs.semantic_search(query, top_k=10)
#         relevant_defects = db.get_defects_by_indices_with_scores(relevant_indices_scores)
#         relevant_defects.sort(key=lambda x: x['relevance_score'], reverse=True)
    
#     response = llm.get_response(query, relevant_defects)
    
#     # Only sanitize if content type is HTML
#     if response.get("content_type") == "html":
#         allowed_tags = ['a', 'p', 'br', 'li', 'ul', 'ol', 'table', 'tr', 'td', 'th', 'thead', 'tbody']
#         allowed_attrs = {'a': ['href', 'target']}
#         response["message"] = bleach.clean(
#             response["message"],
#             tags=allowed_tags,
#             attributes=allowed_attrs,
#             protocols=['http', 'https']
#         )
    
#     return JSONResponse(
#         content={"response": response},
#         headers={"Content-Type": "application/json"}
#     )

# class UVRuleRequest(BaseModel):
#     user_request: str

# @app.post("/proxy/uvrules")
# async def proxy_uvrules(request: UVRuleRequest):
#     """Proxy endpoint for UV Rules service"""
#     if not request.user_request.strip():
#         return JSONResponse(content={
#             "message": "Please provide a policy number and rule code (e.g., E101)."
#         })

#     try:
#         # For now, return a mock response until UV Rules service is available
#         return JSONResponse(content={
#             "message": "I understand you're asking about UV rules. " + 
#                       "To help you better, please provide:\n" +
#                       "1. Policy Number\n" +
#                       "2. Rule Code (e.g., E101)\n\n" +
#                       "For example: 'Why is rule E101 triggered for policy 12345?'"
#         })
#     except Exception as e:
#         return JSONResponse(
#             content={
#                 "message": f"Error processing UV rule request: {str(e)}"
#             },
#             status_code=500
#         )



# class ServiceNowRequest(BaseModel):
#     query: str = None  # Optional: for filtering, you can expand this later

# @app.get("/servicenow/incidents")
# async def get_servicenow_incidents():
#     servicenow_instance = "dev295089.service-now.com"
#     servicenow_username = os.getenv("SERVICENOW_USERNAME", "admin")  # Secure this later!
#     servicenow_password = os.getenv("SERVICENOW_PASSWORD", "WmP!Aw!Y7i7r")  # Secure this later!

#     url = f"https://{servicenow_instance}/api/now/table/incident.json"

#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 url,
#                 auth=(servicenow_username, servicenow_password),
#                 headers={"Accept": "application/json"},
#                 timeout=10.0
#             )
#             response.raise_for_status()
#         return JSONResponse(content=response.json())
#     except httpx.HTTPStatusError as e:
#         return JSONResponse(
#             content={"error": f"ServiceNow API error: {e.response.text}"},
#             status_code=e.response.status_code
#         )
#     except Exception as e:
#         return JSONResponse(
#             content={"error": f"Internal error: {str(e)}"},
#             status_code=500
#         )


# if __name__ == "__main__":
#     try:
#         uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
#     except KeyboardInterrupt:
#         cleanup_resources()



from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import os
import signal
import bleach
import uvicorn
import gc
 
from llm import FAISS, DataBase, LLM
from jira_data_loader import load_data_from_jira
from servicenow import fetch_servicenow_incidents
 
# Global state
defects_llm = {}
valid_defect_ids = set()
cleanup_done = False
 
def cleanup_resources():
    global cleanup_done
    if not cleanup_done:
        defects_llm.clear()
        gc.collect()
        cleanup_done = True
        print("Resources cleaned up.")
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    BASE_DIR = Path(__file__).absolute().parent
    ENV_PATH = os.path.join(BASE_DIR, ".env")
    load_dotenv(ENV_PATH)
    print("App started. Data not loaded yet. Call /defects/load to load data.")
    yield
    cleanup_resources()
 
def handle_exit(signum, frame):
    cleanup_resources()
    raise KeyboardInterrupt()
 
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
 
app = FastAPI(lifespan=lifespan)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
class ChatRequest(BaseModel):
    prompt: str
    conversation_id: str = None
 
class UVRuleRequest(BaseModel):
    user_request: str
 
@app.post("/defects/load")
async def load_defects():
    global valid_defect_ids
    load_data_from_jira()
    vs = FAISS.initialize()
    db = DataBase()
    faiss_data = vs.add_documents(db)
    defects_llm.update(faiss_data)
    valid_defect_ids = {d['bug_id'] for d in db.defect_data}
    return {"message": "Defects loaded successfully.", "valid_ids": list(valid_defect_ids)}
 
@app.post("/defects/response")
async def defects_response(chat_request: ChatRequest):
    llm = LLM()
    query = chat_request.prompt.lower()
    db = DataBase()
 
    mentioned_ids = {word.upper() for word in query.split() if word.upper().startswith('SCRUM-')}
    invalid_ids = mentioned_ids - valid_defect_ids
 
    if invalid_ids:
        return JSONResponse(content={
            "response": {
                "message": f"""**Invalid Defect IDs**
 
The following defect IDs are not in the current database:
- {', '.join(invalid_ids)}
 
**Currently Active Defects:**
- {', '.join(sorted(valid_defect_ids))}
 
---
**Summary:**
Please check the list of active defects above and try your query with a valid defect ID.""",
                "content_type": "markdown"
            }
        })
 
    vs = FAISS.initialize()
    vs.defect_embeddings = defects_llm.get("index")
    relevant_defects = db.defect_data
 
    if any(keyword in query for keyword in ['root', 'cause', 'why', 'solution', 'fix', 'resolve']):
        if mentioned_ids:
            relevant_defects = [d for d in db.defect_data if d['bug_id'] in mentioned_ids]
    elif not any(keyword in query for keyword in ['owner', 'who', 'list', 'all defect']):
        relevant_indices_scores = vs.semantic_search(query, top_k=10)
        relevant_defects = db.get_defects_by_indices_with_scores(relevant_indices_scores)
        relevant_defects.sort(key=lambda x: x['relevance_score'], reverse=True)
 
    response = llm.get_response(query, relevant_defects)
 
    if response.get("content_type") == "html":
        allowed_tags = ['a', 'p', 'br', 'li', 'ul', 'ol', 'table', 'tr', 'td', 'th', 'thead', 'tbody']
        allowed_attrs = {'a': ['href', 'target']}
        response["message"] = bleach.clean(
            response["message"],
            tags=allowed_tags,
            attributes=allowed_attrs,
            protocols=['http', 'https']
        )
 
    return JSONResponse(content={"response": response})
 
@app.post("/proxy/uvrules")
async def proxy_uvrules(request: UVRuleRequest):
    if not request.user_request.strip():
        return JSONResponse(content={
            "message": "Please provide a policy number and rule code (e.g., E101)."
        })
    return JSONResponse(content={
        "message": (
            "I understand you're asking about UV rules. "
            "To help you better, please provide:\n"
            "1. Policy Number\n"
            "2. Rule Code (e.g., E101)\n\n"
            "For example: 'Why is rule E101 triggered for policy 12345?'"
        )
    })
 
@app.get("/servicenow/incidents")
async def get_servicenow_incidents_route():
    try:
        data = await fetch_servicenow_incidents()
        return JSONResponse(content=data)
    except RuntimeError as e:
        return JSONResponse(content={"error": str(e)}, status_code=502)
 
if __name__ == "__main__":
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        cleanup_resources()