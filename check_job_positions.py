from app import app, db
from modules.employees.models import JobPosition, Department

with app.app_context():
    print("Job Positions:")
    job_positions = JobPosition.query.all()
    for jp in job_positions:
        department_name = jp.department.name if jp.department else "None"
        print(f"ID: {jp.id}, Name: {jp.name}, Department: {department_name}, Active: {jp.is_active}")
    
    print("\nDepartments:")
    departments = Department.query.all()
    for dept in departments:
        print(f"ID: {dept.id}, Name: {dept.name}, Active: {dept.is_active}")
