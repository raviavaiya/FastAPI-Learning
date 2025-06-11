from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Load HTML templates from the "templates" directory
templates = Jinja2Templates(directory="templates")

# Serve static files if needed (optional)
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def handle_form(
    request: Request,
    number1: float = Form(...),
    number2: float = Form(...),
    number3: float = Form(...)
):
    total = number1 + number2 + number3
    return templates.TemplateResponse("index.html", {
        "request": request,
        "number1": number1,
        "number2": number2,
        "number3": number3,
        "total": total
    })



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)