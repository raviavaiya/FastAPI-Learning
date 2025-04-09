document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentData = null;
    let columnTypes = {};

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // File upload handling
    document.getElementById('upload-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            showFeedback('upload-feedback', 'Please select a file', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showLoader('upload-loader');
        try {
            const response = await fetch('/upload/', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('upload-feedback', data.error, 'danger');
            } else {
                currentData = data;
                columnTypes = data.column_types;
                showFeedback('upload-feedback', 'File uploaded successfully!', 'success');
                document.getElementById('main-content').style.display = 'block';
                updateDataPreview();
                updateColumnSelections();
            }
        } catch (error) {
            showFeedback('upload-feedback', 'Error uploading file: ' + error.message, 'danger');
        } finally {
            hideLoader('upload-loader');
        }
    });

    // Missing values handling
    document.getElementById('missing-values-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const selectedColumns = getSelectedColumns('missing-columns-selection');
        const method = document.getElementById('missing-method').value;

        if (selectedColumns.length === 0) {
            showFeedback('missing-values-feedback', 'Please select at least one column', 'danger');
            return;
        }

        showLoader('missing-values-loader');
        try {
            const response = await fetch('/preprocess/handle-missing/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'columns': JSON.stringify(selectedColumns),
                    'method': method
                })
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('missing-values-feedback', data.error, 'danger');
            } else {
                showFeedback('missing-values-feedback', data.message, 'success');
                updateDataPreview();
            }
        } catch (error) {
            showFeedback('missing-values-feedback', 'Error processing data: ' + error.message, 'danger');
        } finally {
            hideLoader('missing-values-loader');
        }
    });

    // Normalization handling
    document.getElementById('normalize-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const selectedColumns = getSelectedColumns('normalize-columns-selection');
        const method = document.getElementById('normalize-method').value;

        if (selectedColumns.length === 0) {
            showFeedback('normalize-feedback', 'Please select at least one column', 'danger');
            return;
        }

        showLoader('normalize-loader');
        try {
            const response = await fetch('/preprocess/normalize/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'columns': JSON.stringify(selectedColumns),
                    'method': method
                })
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('normalize-feedback', data.error, 'danger');
            } else {
                showFeedback('normalize-feedback', data.message, 'success');
                updateDataPreview();
            }
        } catch (error) {
            showFeedback('normalize-feedback', 'Error processing data: ' + error.message, 'danger');
        } finally {
            hideLoader('normalize-loader');
        }
    });

    // Categorical encoding handling
    document.getElementById('encoding-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const selectedColumns = getSelectedColumns('categorical-columns-selection');
        const method = document.getElementById('encoding-method').value;

        if (selectedColumns.length === 0) {
            showFeedback('encoding-feedback', 'Please select at least one column', 'danger');
            return;
        }

        showLoader('encoding-loader');
        try {
            const response = await fetch('/preprocess/encode-categorical/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'columns': JSON.stringify(selectedColumns),
                    'method': method
                })
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('encoding-feedback', data.error, 'danger');
            } else {
                showFeedback('encoding-feedback', data.message, 'success');
                updateDataPreview();
                updateColumnSelections();
            }
        } catch (error) {
            showFeedback('encoding-feedback', 'Error processing data: ' + error.message, 'danger');
        } finally {
            hideLoader('encoding-loader');
        }
    });

    // Drop columns handling
    document.getElementById('drop-columns-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const selectedColumns = getSelectedColumns('drop-columns-selection');

        if (selectedColumns.length === 0) {
            showFeedback('drop-columns-feedback', 'Please select at least one column', 'danger');
            return;
        }

        showLoader('drop-columns-loader');
        try {
            const response = await fetch('/preprocess/drop-columns/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'columns': JSON.stringify(selectedColumns)
                })
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('drop-columns-feedback', data.error, 'danger');
            } else {
                showFeedback('drop-columns-feedback', data.message, 'success');
                updateDataPreview();
                updateColumnSelections();
            }
        } catch (error) {
            showFeedback('drop-columns-feedback', 'Error processing data: ' + error.message, 'danger');
        } finally {
            hideLoader('drop-columns-loader');
        }
    });

    // Visualization handling
    document.getElementById('visualization-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const chartType = document.getElementById('chart-type').value;
        const xColumn = document.getElementById('x-column').value;
        const yColumn = document.getElementById('y-column').value;
        const hue = document.getElementById('hue-column').value;
        const title = document.getElementById('chart-title').value;

        if (!xColumn) {
            showFeedback('visualization-feedback', 'Please select an X-axis column', 'danger');
            return;
        }

        showLoader('visualization-loader');
        try {
            const response = await fetch('/visualization/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'chart_type': chartType,
                    'x_column': xColumn,
                    'y_column': yColumn || '',
                    'hue': hue || '',
                    'title': title
                })
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('visualization-feedback', data.error, 'danger');
            } else {
                showFeedback('visualization-feedback', 'Visualization created successfully!', 'success');
                displayVisualization(data.image);
            }
        } catch (error) {
            showFeedback('visualization-feedback', 'Error creating visualization: ' + error.message, 'danger');
        } finally {
            hideLoader('visualization-loader');
        }
    });

    // Download button handling
    document.getElementById('download-btn').addEventListener('click', async function() {
        try {
            const response = await fetch('/data/download/');
            const data = await response.json();
            
            if (data.error) {
                showFeedback('upload-feedback', data.error, 'danger');
            } else {
                const link = document.createElement('a');
                link.href = 'data:text/csv;base64,' + data.content;
                link.download = data.filename;
                link.click();
            }
        } catch (error) {
            showFeedback('upload-feedback', 'Error downloading file: ' + error.message, 'danger');
        }
    });

    // Reset button handling
    document.getElementById('reset-btn').addEventListener('click', async function() {
        try {
            const response = await fetch('/preprocess/reset/', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.error) {
                showFeedback('upload-feedback', data.error, 'danger');
            } else {
                showFeedback('upload-feedback', data.message, 'success');
                updateDataPreview();
                updateColumnSelections();
            }
        } catch (error) {
            showFeedback('upload-feedback', 'Error resetting data: ' + error.message, 'danger');
        }
    });

    // Helper functions
    function showLoader(loaderId) {
        document.getElementById(loaderId).style.display = 'block';
    }

    function hideLoader(loaderId) {
        document.getElementById(loaderId).style.display = 'none';
    }

    function showFeedback(feedbackId, message, type) {
        const feedback = document.getElementById(feedbackId);
        feedback.textContent = message;
        feedback.className = `alert alert-${type} mt-3`;
        feedback.style.display = 'block';
        setTimeout(() => {
            feedback.style.display = 'none';
        }, 5000);
    }

    function getSelectedColumns(containerId) {
        const container = document.getElementById(containerId);
        return Array.from(container.querySelectorAll('.column-badge.selected'))
            .map(badge => badge.dataset.column);
    }

    function updateDataPreview() {
        fetch('/data/preview/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showFeedback('upload-feedback', data.error, 'danger');
                    return;
                }

                // Update dataset information
                document.getElementById('data-filename').textContent = data.filename;
                document.getElementById('data-rows').textContent = data.rows;
                document.getElementById('data-columns-count').textContent = data.columns.length;

                // Update data preview table
                const tableHeader = document.getElementById('data-preview-header');
                const tableBody = document.getElementById('data-preview-body');
                
                // Clear existing content
                tableHeader.innerHTML = '';
                tableBody.innerHTML = '';

                // Add headers
                const headerRow = document.createElement('tr');
                data.columns.forEach(column => {
                    const th = document.createElement('th');
                    th.textContent = column;
                    headerRow.appendChild(th);
                });
                tableHeader.appendChild(headerRow);

                // Add data rows
                data.sample_data.forEach(row => {
                    const tr = document.createElement('tr');
                    data.columns.forEach(column => {
                        const td = document.createElement('td');
                        td.textContent = row[column];
                        tr.appendChild(td);
                    });
                    tableBody.appendChild(tr);
                });
            })
            .catch(error => {
                showFeedback('upload-feedback', 'Error updating data preview: ' + error.message, 'danger');
            });
    }

    function updateColumnSelections() {
        fetch('/data/preview/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showFeedback('upload-feedback', data.error, 'danger');
                    return;
                }

                // Update column selections for all forms
                updateColumnSelection('missing-columns-selection', data.columns);
                updateColumnSelection('normalize-columns-selection', data.columns.filter(col => columnTypes[col] === 'numeric'));
                updateColumnSelection('categorical-columns-selection', data.columns.filter(col => columnTypes[col] === 'categorical'));
                updateColumnSelection('drop-columns-selection', data.columns);

                // Update visualization column selections
                updateVisualizationColumns(data.columns);
            })
            .catch(error => {
                showFeedback('upload-feedback', 'Error updating column selections: ' + error.message, 'danger');
            });
    }

    function updateColumnSelection(containerId, columns) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        columns.forEach(column => {
            const badge = document.createElement('span');
            badge.className = `column-badge ${columnTypes[column]}`;
            badge.dataset.column = column;
            badge.textContent = column;
            badge.addEventListener('click', function() {
                this.classList.toggle('selected');
            });
            container.appendChild(badge);
        });
    }

    function updateVisualizationColumns(columns) {
        const xColumnSelect = document.getElementById('x-column');
        const yColumnSelect = document.getElementById('y-column');
        const hueColumnSelect = document.getElementById('hue-column');

        // Clear existing options
        xColumnSelect.innerHTML = '<option value="" selected disabled>Select column</option>';
        yColumnSelect.innerHTML = '<option value="" selected disabled>Select column (optional)</option>';
        hueColumnSelect.innerHTML = '<option value="" selected disabled>Select column (optional)</option>';

        // Add new options
        columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            xColumnSelect.appendChild(option.cloneNode(true));
            yColumnSelect.appendChild(option.cloneNode(true));
            hueColumnSelect.appendChild(option.cloneNode(true));
        });
    }

    function displayVisualization(imageData) {
        const gallery = document.getElementById('visualization-gallery');
        const img = document.createElement('img');
        img.src = imageData;
        img.className = 'img-fluid';
        gallery.appendChild(img);
    }
}); 