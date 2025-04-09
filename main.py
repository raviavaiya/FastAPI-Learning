from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Tea(BaseModel):
    id: int
    name: str
    origin: str

teas: List[Tea] = []

@app.get("/")
def read_root():
    return {"message": "Welcome To Tea House"}

@app.get("/teas/")
def get_teas():
    return teas

@app.post("/teas/")
def add_tea(tea: Tea):
    teas.append(tea)
    return tea

@app.put("/teas/{tea_id}")
def update_tea(tea_id: int, updated_tea: Tea):
    for index, tea in enumerate(teas):
        if tea.id == tea_id:
            teas[index] = updated_tea
            return updated_tea
    return {"error": "Tea not found"}

@app.delete("/teas/{tea_id}")
def delete_tea(tea_id: int):
    for index, tea in enumerate(teas):
        if tea.id == tea_id:
            deleted=teas.pop(index)
            return {"message": "{} deleted successfully".format(deleted)}
    return {"error": "Tea not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

