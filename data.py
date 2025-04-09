# main.py
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import io
import os
import json
from typing import List, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import is_numeric_dtype

# Create FastAPI app
app = FastAPI(title="Data Preprocessing and Visualization App")

# Create templates and static directories if they don't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create an in-memory store for the uploaded file
uploaded_file = {"dataframe": None, "filename": None, "preprocessed": None}

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
        uploaded_file["preprocessed"] = df.copy()  # Initialize preprocessed with original
        
        # Get column types
        column_types = {}
        for col in df.columns:
            if is_numeric_dtype(df[col]):
                column_types[col] = "numeric"
            else:
                column_types[col] = "categorical"
        
        # Basic dataset info
        info = {
            "columns": df.columns.tolist(),
            "column_types": column_types,
            "rows": len(df),
            "filename": file.filename,
            "missing_values": df.isna().sum().to_dict(),
            "sample_data": df.head(5).to_dict(orient="records")
        }
        
        return info
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}

@app.post("/preprocess/handle-missing/")
async def handle_missing_values(columns: List[str] = Form(...), method: str = Form(...)):
    try:
        df = uploaded_file["preprocessed"]
        if df is None:
            return {"error": "No file has been uploaded yet."}
        
        # Validate columns
        for col in columns:
            if col not in df.columns:
                return {"error": f"Column '{col}' not found in the dataset."}
        
        # Apply imputation based on method
        for col in columns:
            if method == "mean" and is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            elif method == "median" and is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            elif method == "mode":
                df[col] = df[col].fillna(df[col].mode()[0])
            elif method == "constant":
                df[col] = df[col].fillna(0 if is_numeric_dtype(df[col]) else "unknown")
            elif method == "drop_rows":
                df = df.dropna(subset=columns)
            else:
                return {"error": f"Invalid method '{method}' for column '{col}'."}
        
        # Update the preprocessed dataframe
        uploaded_file["preprocessed"] = df
        
        return {
            "success": True,
            "message": f"Successfully handled missing values in {len(columns)} column(s) using {method} method.",
            "rows": len(df),
            "missing_values": df.isna().sum().to_dict()
        }
    except Exception as e:
        return {"error": f"Error handling missing values: {str(e)}"}

@app.post("/preprocess/normalize/")
async def normalize_columns(columns: List[str] = Form(...), method: str = Form(...)):
    try:
        df = uploaded_file["preprocessed"]
        if df is None:
            return {"error": "No file has been uploaded yet."}
        
        # Validate columns are numeric
        for col in columns:
            if col not in df.columns:
                return {"error": f"Column '{col}' not found in the dataset."}
            if not is_numeric_dtype(df[col]):
                return {"error": f"Column '{col}' is not numeric and cannot be normalized."}
        
        # Apply normalization based on method
        if method == "minmax":
            scaler = MinMaxScaler()
            df[columns] = scaler.fit_transform(df[columns])
        elif method == "standard":
            scaler = StandardScaler()
            df[columns] = scaler.fit_transform(df[columns])
        elif method == "robust":
            scaler = RobustScaler()
            df[columns] = scaler.fit_transform(df[columns])
        else:
            return {"error": f"Invalid normalization method '{method}'."}
        
        # Update the preprocessed dataframe
        uploaded_file["preprocessed"] = df
        
        # Get sample of normalized data
        sample_data = df[columns].head(5).to_dict(orient="records")
        
        return {
            "success": True,
            "message": f"Successfully normalized {len(columns)} column(s) using {method} method.",
            "sample_data": sample_data
        }
    except Exception as e:
        return {"error": f"Error normalizing data: {str(e)}"}

@app.post("/preprocess/encode-categorical/")
async def encode_categorical(columns: List[str] = Form(...), method: str = Form(...)):
    try:
        df = uploaded_file["preprocessed"]
        if df is None:
            return {"error": "No file has been uploaded yet."}
        
        # Validate columns
        for col in columns:
            if col not in df.columns:
                return {"error": f"Column '{col}' not found in the dataset."}
        
        # Apply encoding based on method
        if method == "onehot":
            # One-hot encoding
            for col in columns:
                # Get dummies and join with original dataframe
                dummies = pd.get_dummies(df[col], prefix=col)
                df = pd.concat([df.drop(col, axis=1), dummies], axis=1)
        elif method == "label":
            # Label encoding
            for col in columns:
                # Map each unique value to a number
                categories = df[col].astype('category').cat.categories
                df[col] = df[col].astype('category').cat.codes
        else:
            return {"error": f"Invalid encoding method '{method}'."}
        
        # Update the preprocessed dataframe
        uploaded_file["preprocessed"] = df
        
        # Get new column list after encoding
        new_columns = df.columns.tolist()
        
        return {
            "success": True,
            "message": f"Successfully encoded {len(columns)} column(s) using {method} method.",
            "new_columns": new_columns,
            "sample_data": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        return {"error": f"Error encoding categorical data: {str(e)}"}

@app.post("/preprocess/drop-columns/")
async def drop_columns(columns: List[str] = Form(...)):
    try:
        df = uploaded_file["preprocessed"]
        if df is None:
            return {"error": "No file has been uploaded yet."}
        
        # Validate columns
        for col in columns:
            if col not in df.columns:
                return {"error": f"Column '{col}' not found in the dataset."}
        
        # Drop columns
        df = df.drop(columns=columns)
        
        # Update the preprocessed dataframe
        uploaded_file["preprocessed"] = df
        
        # Get new column list after dropping
        new_columns = df.columns.tolist()
        
        return {
            "success": True,
            "message": f"Successfully dropped {len(columns)} column(s).",
            "new_columns": new_columns,
            "rows": len(df)
        }
    except Exception as e:
        return {"error": f"Error dropping columns: {str(e)}"}

@app.post("/visualization/create/")
async def create_visualization(
    chart_type: str = Form(...), 
    x_column: str = Form(...),
    y_column: Optional[str] = Form(None),
    hue: Optional[str] = Form(None),
    title: str = Form(...)
):
    try:
        df = uploaded_file["preprocessed"]
        if df is None:
            return {"error": "No file has been uploaded yet."}
        
        # Validate columns
        if x_column not in df.columns:
            return {"error": f"Column '{x_column}' not found in the dataset."}
        
        if y_column and y_column not in df.columns:
            return {"error": f"Column '{y_column}' not found in the dataset."}
        
        if hue and hue not in df.columns:
            return {"error": f"Column '{hue}' not found in the dataset."}
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Create appropriate plot based on chart type
        if chart_type == "bar":
            if not y_column:
                return {"error": "Y-axis column is required for bar chart."}
            sns.barplot(x=x_column, y=y_column, hue=hue, data=df)
        elif chart_type == "histogram":
            sns.histplot(df[x_column], kde=True)
        elif chart_type == "scatter":
            if not y_column:
                return {"error": "Y-axis column is required for scatter plot."}
            sns.scatterplot(x=x_column, y=y_column, hue=hue, data=df)
        elif chart_type == "box":
            sns.boxplot(x=x_column, y=y_column, hue=hue, data=df)
        elif chart_type == "line":
            if not y_column:
                return {"error": "Y-axis column is required for line chart."}
            sns.lineplot(x=x_column, y=y_column, hue=hue, data=df)
        elif chart_type == "heatmap":
            # For heatmap, we need to create a correlation matrix
            corr_matrix = df.corr()
            sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")
        elif chart_type == "pairplot":
            # For pairplot, create a new figure with seaborn directly
            # We'll limit to 5 columns to avoid too many plots
            numeric_cols = [col for col in df.columns if is_numeric_dtype(df[col])]
            if len(numeric_cols) > 5:
                numeric_cols = numeric_cols[:5]
                
            g = sns.pairplot(df[numeric_cols], hue=hue if hue in numeric_cols else None)
            plt.close(g.fig)  # Close the original figure
            
            # Save the pairplot figure
            buf = BytesIO()
            g.savefig(buf, format="png")
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return {"image": f"data:image/png;base64,{img_str}", "success": True}
        else:
            return {"error": f"Unsupported chart type: {chart_type}"}
        
        # Set title
        plt.title(title)
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return {"image": f"data:image/png;base64,{img_str}", "success": True}
    except Exception as e:
        return {"error": f"Error creating visualization: {str(e)}"}

@app.get("/data/preview/")
async def get_data_preview():
    df = uploaded_file["preprocessed"]
    if df is None:
        return {"error": "No file has been uploaded yet."}
    
    # Get basic info about preprocessed data
    return {
        "columns": df.columns.tolist(),
        "rows": len(df),
        "sample_data": df.head(10).to_dict(orient="records"),
        "missing_values": df.isna().sum().to_dict(),
        "success": True
    }

@app.get("/data/download/")
async def download_preprocessed_data():
    df = uploaded_file["preprocessed"]
    if df is None:
        return {"error": "No file has been uploaded yet."}
    
    # Convert to CSV
    csv_content = df.to_csv(index=False)
    # Encode as base64
    b64_content = base64.b64encode(csv_content.encode()).decode()
    
    return {
        "filename": "preprocessed_" + uploaded_file["filename"],
        "content": b64_content,
        "success": True
    }

@app.post("/preprocess/reset/")
async def reset_preprocessing():
    try:
        # Reset preprocessed to original
        if uploaded_file["dataframe"] is not None:
            uploaded_file["preprocessed"] = uploaded_file["dataframe"].copy()
            
            return {
                "success": True,
                "message": "Preprocessing has been reset to original data.",
                "columns": uploaded_file["preprocessed"].columns.tolist(),
                "rows": len(uploaded_file["preprocessed"])
            }
        else:
            return {"error": "No file has been uploaded yet."}
    except Exception as e:
        return {"error": f"Error resetting preprocessing: {str(e)}"}

# Create the HTML template file
with open("templates/index.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Preprocessing and Visualization</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body {
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container-fluid {
            max-width: 1400px;
        }
        .card {
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .chart-container {
            margin-bottom: 30px;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
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
        .nav-tabs .nav-link {
            border-radius: 8px 8px 0 0;
        }
        .nav-tabs .nav-link.active {
            font-weight: bold;
            background-color: #fff;
            border-bottom-color: #fff;
        }
        #visualization-gallery {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
        }
        .table-responsive {
            max-height: 400px;
            overflow-y: auto;
        }
        .column-badge {
            display: inline-block;
            margin: 5px;
            padding: 5px 10px;
            border-radius: 20px;
            background-color: #e9ecef;
            cursor: pointer;
        }
        .column-badge.selected {
            background-color: #0d6efd;
            color: white;
        }
        .column-badge.numeric {
            border-left: 4px solid #28a745;
        }
        .column-badge.categorical {
            border-left: 4px solid #dc3545;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="text-center mb-4">Data Preprocessing and Visualization</h1>
        
        <!-- Upload Section -->
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Dataset Upload</h5>
                <form id="upload-form">
                    <div class="mb-3">
                        <input type="file" class="form-control" id="file-input" accept=".csv,.xlsx,.xls" required>
                        <div class="form-text">Supported formats: CSV, Excel (.xlsx, .xls)</div>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-upload"></i> Upload
                    </button>
                </form>
                <div id="upload-loader" class="loader"></div>
                <div id="upload-feedback" class="alert mt-3" style="display: none;"></div>
            </div>
        </div>
        
        <!-- Main Content (hidden until file is uploaded) -->
        <div id="main-content" style="display: none;">
            <ul class="nav nav-tabs" id="myTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="data-tab" data-bs-toggle="tab" data-bs-target="#data" type="button" role="tab" aria-controls="data" aria-selected="true">
                        <i class="fas fa-table"></i> Data Preview
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="preprocess-tab" data-bs-toggle="tab" data-bs-target="#preprocess" type="button" role="tab" aria-controls="preprocess" aria-selected="false">
                        <i class="fas fa-cogs"></i> Preprocessing
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="visualize-tab" data-bs-toggle="tab" data-bs-target="#visualize" type="button" role="tab" aria-controls="visualize" aria-selected="false">
                        <i class="fas fa-chart-bar"></i> Visualization
                    </button>
                </li>
            </ul>
            
            <div class="tab-content" id="myTabContent">
                <!-- Data Preview Tab -->
                <div class="tab-pane fade show active" id="data" role="tabpanel" aria-labelledby="data-tab">
                    <div class="card mt-3">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5 class="card-title">Dataset Information</h5>
                                    <p><strong>Filename:</strong> <span id="data-filename"></span></p>
                                    <p><strong>Rows:</strong> <span id="data-rows"></span></p>
                                    <p><strong>Columns:</strong> <span id="data-columns-count"></span></p>
                                    <div>
                                        <strong>Column List:</strong>
                                        <div id="data-columns-list" class="mt-2"></div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h5>Missing Values</h5>
                                    <div id="missing-values" class="table-responsive">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Column</th>
                                                    <th>Missing Count</th>
                                                </tr>
                                            </thead>
                                            <tbody id="missing-values-body"></tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            
                            <h5 class="mt-4">Data Sample</h5>
                            <div class="table-responsive">
                                <table class="table table-striped table-hover" id="data-preview-table">
                                    <thead id="data-preview-header"></thead>
                                    <tbody id="data-preview-body"></tbody>
                                </table>
                            </div>
                            
                            <div class="mt-3">
                                <button class="btn btn-success" id="download-btn">
                                    <i class="fas fa-download"></i> Download Processed Data
                                </button>
                                <button class="btn btn-secondary" id="reset-btn">
                                    <i class="fas fa-undo"></i> Reset to Original
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Preprocessing Tab -->
                <div class="tab-pane fade" id="preprocess" role="tabpanel" aria-labelledby="preprocess-tab">
                    <div class="row mt-3">
                        <!-- Missing Values -->
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Handle Missing Values</h5>
                                    <form id="missing-values-form">
                                        <div class="mb-3">
                                            <label class="form-label">Select Columns</label>
                                            <div id="missing-columns-selection"></div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="missing-method" class="form-label">Method</label>
                                            <select class="form-select" id="missing-method" required>
                                                <option value="" selected disabled>Select method</option>
                                                <option value="mean">Mean (numeric only)</option>
                                                <option value="median">Median (numeric only)</option>
                                                <option value="mode">Mode (most frequent value)</option>
                                                <option value="constant">Fill with constant (0 or "unknown")</option>
                                                <option value="drop_rows">Drop rows with missing values</option>
                                            </select>
                                        </div>
                                        <button type="submit" class="btn btn-primary">Apply</button>
                                    </form>
                                    <div id="missing-values-loader" class="loader"></div>
                                    <div id="missing-values-feedback" class="alert mt-3" style="display: none;"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Normalization -->
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Normalize Data</h5>
                                    <form id="normalize-form">
                                        <div class="mb-3">
                                            <label class="form-label">Select Numeric Columns</label>
                                            <div id="normalize-columns-selection"></div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="normalize-method" class="form-label">Method</label>
                                            <select class="form-select" id="normalize-method" required>
                                                <option value="" selected disabled>Select method</option>
                                                <option value="minmax">Min-Max Scaling (0-1)</option>
                                                <option value="standard">Standard Scaling (z-score)</option>
                                                <option value="robust">Robust Scaling (using quantiles)</option>
                                            </select>
                                        </div>
                                        <button type="submit" class="btn btn-primary">Apply</button>
                                    </form>
                                    <div id="normalize-loader" class="loader"></div>
                                    <div id="normalize-feedback" class="alert mt-3" style="display: none;"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Categorical Encoding -->
                        <div class="col-md-6 mt-4">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Encode Categorical Data</h5>
                                    <form id="encoding-form">
                                        <div class="mb-3">
                                            <label class="form-label">Select Categorical Columns</label>
                                            <div id="categorical-columns-selection"></div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="encoding-method" class="form-label">Method</label>
                                            <select class="form-select" id="encoding-method" required>
                                                <option value="" selected disabled>Select method</option>
                                                <option value="onehot">One-Hot Encoding</option>
                                                <option value="label">Label Encoding</option>
                                            </select>
                                        </div>
                                        <button type="submit" class="btn btn-primary">Apply</button>
                                    </form>
                                    <div id="encoding-loader" class="loader"></div>
                                    <div id="encoding-feedback" class="alert mt-3" style="display: none;"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Drop Columns -->
                        <div class="col-md-6 mt-4">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Drop Columns</h5>
                                    <form id="drop-columns-form">
                                        <div class="mb-3">
                                            <label class="form-label">Select Columns to Drop</label>
                                            <div id="drop-columns-selection"></div>
                                        </div>
                                        <button type="submit" class="btn btn-danger">Drop Selected Columns</button>
                                    </form>
                                    <div id="drop-columns-loader" class="loader"></div>
                                    <div id="drop-columns-feedback" class="alert mt-3" style="display: none;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Visualization Tab -->
                <div class="tab-pane fade" id="visualize" role="tabpanel" aria-labelledby="visualize-tab">
                    <div class="card mt-3">
                        <div class="card-body">
                            <h5 class="card-title">Create Visualization</h5>
                            <form id="visualization-form" class="row">
                                <div class="col-md-4 mb-3">
                                    <label for="chart-type" class="form-label">Chart Type</label>
                                    <select class="form-select" id="chart-type" required>
                                        <option value="" selected disabled>Select chart type</option>
                                        <option value="bar">Bar Chart</option>
                                        <option value="histogram">Histogram</option>
                                        <option value="scatter">Scatter Plot</option>
                                        <option value="box">Box Plot</option>
                                        <option value="line">Line Chart</option>
                                        <option value="heatmap">Correlation Heatmap</option>
                                        <option value="pairplot">Pair Plot</option>
                                    </select>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <label for="x-column" class="form-label">X-Axis Column</label>
                                    <select class="form-select" id="x-column" required>
                                        <option value="" selected disabled>Select column</option>
                                    </select>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <label for="y-column" class="form-label">Y-Axis Column</label>
                                    <select class="form-select" id="y-column">
                                        <option value="" selected disabled>Select column (optional)</option>
                                    </select>
                                    <small class="form-text text-muted">Required for Bar, Scatter, Box, and Line charts</small>
                                </div>
                                
                                <div class="col-md-8 mb-3">
                                    <label for="chart-title" class="form-label">Chart Title</label>
                                    <input type="text" class="form-control" id="chart-title" placeholder="Enter chart title" required>
                                </div>
                                
                                <div class="col-md-4 mb-3">
                                    <label for="hue-column" class="form-label">Color By (Hue)</label>
                                    <select class="form-select" id="hue-column">
                                        <option value="" selected disabled>Select column (optional)</option>
                                    </select>
                                </div>
                                
                                <div class="col-12">
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fas fa-chart-line"></i> Create Visualization
                                    </button>
                                </div>
                            </form>
                            <div id="visualization-loader" class="loader"></div>
                            <div id="visualization-feedback" class="alert mt-3" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <!-- Visualization Gallery -->
                    <div id="visualization-gallery"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JavaScript -->
    <script src="/static/js/main.js"></script>
</body>
</html>
    
""")
    