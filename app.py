# main.py
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
import statistics
from collections import Counter
import os

# Create FastAPI app
app = FastAPI(title="Dataset Statistics Calculator")

# Create templates and static directories if they don't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create an in-memory store for the uploaded file
uploaded_file = {"dataframe": None, "filename": None}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read the file content
        contents = await file.read()
        buffer = io.BytesIO(contents)
        
        # Check file extension to determine how to read it
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(buffer)
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(buffer)
        else:
            return {"error": "Unsupported file format. Please upload CSV or Excel files."}
        
        # Store the dataframe in memory
        uploaded_file["dataframe"] = df
        uploaded_file["filename"] = file.filename
        
        # Return the columns for selection
        return {"columns": df.columns.tolist(), "filename": file.filename}
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}

@app.post("/calculate-statistics/")
async def calculate_statistics(column_name: str = Form(...)):
    try:
        df = uploaded_file["dataframe"]
        if df is None:
            return {"error": "No file has been uploaded yet."}
        
        if column_name not in df.columns:
            return {"error": f"Column '{column_name}' not found in the dataset."}
        
        # Extract the column
        column = df[column_name]
        
        # Check if column contains numeric data
        if not pd.api.types.is_numeric_dtype(column):
            return {"error": f"Column '{column_name}' does not contain numeric data."}
        
        # Calculate statistics
        mean = float(column.mean())
        median = float(column.median())
        
        # Calculate mode - might be multiple values
        mode_result = statistics.multimode(column)
        mode = [float(m) for m in mode_result]
        
        # Get a sample of the data for display
        sample_data = column.head(5).tolist()
        
        return {
            "mean": mean,
            "median": median,
            "mode": mode,
            "sample_data": sample_data
        }
    except Exception as e:
        return {"error": f"Error calculating statistics: {str(e)}"}

# Create the HTML template file
with open("templates/index.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dataset Statistics Calculator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 800px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        .stat-card {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f8f9fa;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #0d6efd;
        }
        #results {
            display: none;
            margin-top: 30px;
        }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 2s linear infinite;
            display: none;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Dataset Statistics Calculator</h1>
        
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Step 1: Upload Dataset</h5>
                <form id="upload-form">
                    <div class="mb-3">
                        <input type="file" class="form-control" id="file-input" accept=".csv,.xlsx,.xls" required>
                        <div class="form-text">Supported formats: CSV, Excel (.xlsx, .xls)</div>
                    </div>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </form>
                <div id="upload-loader" class="loader"></div>
                <div id="upload-feedback" class="alert mt-3" style="display: none;"></div>
            </div>
        </div>
        
        <div id="column-selection" class="card mb-4" style="display: none;">
            <div class="card-body">
                <h5 class="card-title">Step 2: Select Column for Analysis</h5>
                <form id="stats-form">
                    <div class="mb-3">
                        <select class="form-select" id="column-select" required>
                            <option value="" selected disabled>Select a column</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-success">Calculate Statistics</button>
                </form>
                <div id="calc-loader" class="loader"></div>
            </div>
        </div>
        
        <div id="results">
            <h5 class="mb-3">Statistical Results:</h5>
            <div class="row">
                <div class="col-md-4">
                    <div class="stat-card text-center">
                        <h6>Mean</h6>
                        <div id="mean-value" class="stat-value">--</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card text-center">
                        <h6>Median</h6>
                        <div id="median-value" class="stat-value">--</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card text-center">
                        <h6>Mode</h6>
                        <div id="mode-value" class="stat-value">--</div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h6>Sample Data:</h6>
                <ul id="sample-data" class="list-group">
                </ul>
            </div>
        </div>
        
        <div id="error-message" class="alert alert-danger mt-3" style="display: none;"></div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const uploadForm = document.getElementById('upload-form');
            const statsForm = document.getElementById('stats-form');
            const uploadLoader = document.getElementById('upload-loader');
            const calcLoader = document.getElementById('calc-loader');
            const columnSelection = document.getElementById('column-selection');
            const columnSelect = document.getElementById('column-select');
            const results = document.getElementById('results');
            const errorMessage = document.getElementById('error-message');
            const uploadFeedback = document.getElementById('upload-feedback');

            // Handle file upload
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const fileInput = document.getElementById('file-input');
                const file = fileInput.files[0];
                
                if (!file) {
                    showError('Please select a file to upload.');
                    return;
                }
                
                // Create form data
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    uploadLoader.style.display = 'block';
                    errorMessage.style.display = 'none';
                    
                    const response = await fetch('/upload/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        showError(data.error);
                    } else {
                        // Show success message
                        uploadFeedback.textContent = `Successfully uploaded ${data.filename}`;
                        uploadFeedback.className = 'alert alert-success mt-3';
                        uploadFeedback.style.display = 'block';
                        
                        // Populate column dropdown
                        columnSelect.innerHTML = '<option value="" selected disabled>Select a column</option>';
                        data.columns.forEach(column => {
                            const option = document.createElement('option');
                            option.value = column;
                            option.textContent = column;
                            columnSelect.appendChild(option);
                        });
                        
                        // Show column selection
                        columnSelection.style.display = 'block';
                    }
                } catch (error) {
                    showError('Error uploading file: ' + error.message);
                } finally {
                    uploadLoader.style.display = 'none';
                }
            });
            
            // Handle statistics calculation
            statsForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const columnName = columnSelect.value;
                
                if (!columnName) {
                    showError('Please select a column.');
                    return;
                }
                
                // Create form data
                const formData = new FormData();
                formData.append('column_name', columnName);
                
                try {
                    calcLoader.style.display = 'block';
                    errorMessage.style.display = 'none';
                    results.style.display = 'none';
                    
                    const response = await fetch('/calculate-statistics/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        showError(data.error);
                    } else {
                        // Update results
                        document.getElementById('mean-value').textContent = data.mean.toFixed(2);
                        document.getElementById('median-value').textContent = data.median.toFixed(2);
                        
                        // Handle mode (could be multiple values)
                        const modeValue = document.getElementById('mode-value');
                        if (data.mode.length === 1) {
                            modeValue.textContent = data.mode[0].toFixed(2);
                        } else {
                            modeValue.textContent = data.mode.map(m => m.toFixed(2)).join(', ');
                        }
                        
                        // Update sample data
                        const sampleDataList = document.getElementById('sample-data');
                        sampleDataList.innerHTML = '';
                        data.sample_data.forEach(value => {
                            const listItem = document.createElement('li');
                            listItem.className = 'list-group-item';
                            listItem.textContent = value;
                            sampleDataList.appendChild(listItem);
                        });
                        
                        // Show results
                        results.style.display = 'block';
                    }
                } catch (error) {
                    showError('Error calculating statistics: ' + error.message);
                } finally {
                    calcLoader.style.display = 'none';
                }
            });
            
            function showError(message) {
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
            }
        });
    </script>
</body>
</html>
    """)

# Create a README file with instructions
with open("README.md", "w") as f:
    f.write("""
# Dataset Statistics Calculator

A web application built with FastAPI that allows users to upload datasets and calculate basic statistical measures (mean, median, and mode) for selected columns.

## Features

- Upload CSV or Excel (.xlsx, .xls) files
- Select columns for statistical analysis
- Calculate mean, median, and mode
- View sample data from the selected column
- Responsive web interface

## Requirements

- Python 3.7 or higher
- FastAPI
- Pandas
- Jinja2

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install fastapi uvicorn pandas jinja2 python-multipart openpyxl
```

## Running the Application

```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## Usage

1. Open your web browser and navigate to `http://localhost:8000`
2. Upload a dataset file (CSV or Excel)
3. Select a column to analyze
4. View the statistical results

## Notes

- The application only processes numeric columns for statistical analysis
- Large files might take longer to process
- The application stores the dataset in memory during the session
""")