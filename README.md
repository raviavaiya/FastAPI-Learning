
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
