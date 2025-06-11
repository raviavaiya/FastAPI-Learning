from fastapi import FastAPI, Request, Form
import mysql.connector
import pandas as pd
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()
templates = Jinja2Templates(directory="static")  # Your HTML should be inside static/index.html

# Function to fetch all products
def get_all_products():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="food_system"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_product")
    data = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(data, columns=['id', 'p_name', 'p_type', 'protin', 'fat', 'carbos', 'description'])
    return df.to_dict(orient="records")

# GET request to load all products
@app.get("/", response_class=HTMLResponse)
def show_products(request: Request):
    data = get_all_products()
    return templates.TemplateResponse("index.html", {"request": request, "products": data})


# Function to filter products based on nutrition values
@app.post("/submit", response_class=HTMLResponse)
async def handle_form(
    request: Request,
    protin: float = Form(...),
    fat: float = Form(...),
    carbos: float = Form(...)
):
    df = pd.read_csv('D:\\FastAPI-Learning\\Indian_Food_Nutrition_Processed_Cleaned.csv')
    data = get_all_products()
    # Vector space for similarity
    X = df[["Carbohydrates (g)", "Protein (g)", "Fats (g)"]].values
    target = [[carbos, protin, fat]]
    similarity_scores = cosine_similarity(target, X)[0]
    top_5_indices = similarity_scores.argsort()[::][::-1]
    top_5_products = [data[i] for i in top_5_indices]
    return templates.TemplateResponse("index.html", {"request": request, "products": top_5_products})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)