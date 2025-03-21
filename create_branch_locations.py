from app import create_app, db
from modules.inventory.models import StockLocation
from modules.auth.models import Branch

app = create_app()
with app.app_context():
    # Get all branches
    branches = Branch.query.all()
    print(f"Found {len(branches)} branches")
    
    # Get all stock locations
    locations = StockLocation.query.all()
    print(f"Found {len(locations)} stock locations")
    
    # Print current locations with their branch assignments
    print("\nCurrent Stock Locations:")
    for loc in locations:
        branch_name = "No Branch"
        if loc.branch_id:
            branch = Branch.query.get(loc.branch_id)
            if branch:
                branch_name = branch.name
        print(f"ID: {loc.id}, Name: {loc.name}, Type: {loc.location_type}, Branch: {branch_name}")
    
    # Create branch-specific locations for each branch
    for branch in branches:
        print(f"\nChecking locations for branch: {branch.name}")
        
        # Check if branch already has the standard location types
        location_types = {
            'supplier': f"Supplier (supplier)",
            'internal': f"Main Stock (internal)",
            'internal_shop': f"Shop Floor (internal)",
            'customer': f"Customers (customer)",
            'inventory_loss': f"Inventory Loss (inventory loss)",
            'quality': f"Quality Control (internal)"
        }
        
        for loc_type, loc_name in location_types.items():
            # Check if this location type already exists for this branch
            existing = StockLocation.query.filter_by(
                branch_id=branch.id,
                location_type=loc_type.split('_')[0]  # Handle 'internal_shop' -> 'internal'
            ).first()
            
            if existing:
                print(f"  ✓ {loc_name} already exists for {branch.name}")
            else:
                # Create the location for this branch
                new_location = StockLocation(
                    name=loc_name.split(' (')[0],  # Get name without type
                    location_type=loc_type.split('_')[0],  # Handle 'internal_shop' -> 'internal'
                    branch_id=branch.id
                )
                db.session.add(new_location)
                print(f"  + Created {loc_name} for {branch.name}")
        
    # Commit all changes
    db.session.commit()
    print("\nAll branch-specific locations have been created!")
    
    # Verify the results
    print("\nVerifying results:")
    for branch in branches:
        locations = StockLocation.query.filter_by(branch_id=branch.id).all()
        print(f"Branch '{branch.name}' has {len(locations)} locations:")
        for loc in locations:
            print(f"  - {loc.name} ({loc.location_type})")
