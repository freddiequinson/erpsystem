import pandas as pd

# Create a simple DataFrame with product data
data = {
    'sku': ['P001', 'P002', 'P003', 'P004', 'P005'],
    'name': ['Test Product 1', 'Test Product 2', 'Test Product 3', 'Test Product 4', 'Test Product 5'],
    'description': ['Description for product 1', 'Description for product 2', 'Description for product 3', 'Description for product 4', 'Description for product 5'],
    'category': ['Electronics', 'Office Supplies', 'Electronics', 'Furniture', 'Office Supplies'],
    'cost_price': [10.50, 5.25, 15.75, 100.00, 8.99],
    'sale_price': [19.99, 9.99, 29.99, 199.99, 14.99],
    'min_stock': [5, 10, 3, 2, 8],
    'max_stock': [50, 100, 30, 20, 80],
    'weight': [0.5, 0.2, 0.8, 15.0, 0.3],
    'volume': [0.01, 0.005, 0.02, 0.5, 0.008],
    'is_active': [True, True, True, True, True],
    'barcode': ['BAR001', 'BAR002', 'BAR003', 'BAR004', 'BAR005']
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel('test_products.xlsx', index=False)

print("Test products Excel file created successfully!")
