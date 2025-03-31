# Enterprise Resource Planning (ERP) System

A comprehensive ERP system inspired by Odoo Enterprise, designed to manage inventory, sales, point of sales, reporting, purchasing, and employee management.

## Features

- **Inventory Management**: Track stock levels, movements, and valuations in real-time
- **Sales Management**: Manage quotes, orders, and customer relationships
- **Point of Sales (POS)**: User-friendly interface for retail operations
- **Reporting**: Generate comprehensive reports for business insights
- **Purchase Management**: Handle vendor relationships and procurement
- **Employee Management**: Track employee information, attendance, and performance

## Technical Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite (for development), PostgreSQL (recommended for production)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap and DataTables for Excel-like interfaces
- **Authentication**: JWT (JSON Web Tokens)

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize the database: `python init_db.py`
4. Run the application: `python app.py`
5. Access the application at `http://localhost:5000`

## Deployment to PythonAnywhere

1. Create a PythonAnywhere account at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Open a Bash console in PythonAnywhere
3. Clone the repository: 
4. Set up a virtual environment:
   ```
   cd odoo-clone
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Create a web app via the Web tab:
   - Select "Manual Configuration" (not Flask)
   - Choose Python version (3.8 or higher)
6. Configure the WSGI file:
   - Set the path to your application
   - Make sure it points to your app object
7. Initialize the database: `python init_db.py`
8. Reload the web app

## Project Structure

```
erp-system/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── init_db.py              # Database initialization script
├── requirements.txt        # Python dependencies
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
└── modules/                # Application modules
    ├── auth/               # Authentication module
    ├── inventory/          # Inventory management module
    ├── sales/              # Sales management module
    ├── pos/                # Point of Sales module
    ├── reporting/          # Reporting module
    ├── purchase/           # Purchase management module
    └── employees/          # Employee management module
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
