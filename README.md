# Waste Management Database

A PostgreSQL-based project modeling the operations of a waste-collection service.  
It showcases relational schema design, data modeling, and SQL programming through
Python (psycopg2), making it a strong demonstration of SQL expertise.

## Project Structure
- `waste_wrangler_schema.sql` – DDL for all relations.
- `waste_wrangler_data.sql` – Sample data for testing.
- `main.py` / `a2.py` – Python interface (`WasteWrangler` class) that executes SQL
  operations such as scheduling trips, assigning technicians, and rerouting waste.

## Database Schema Overview
The schema captures trucks, employees, facilities, routes, and trips:

| Table         | Description |
|---------------|-------------|
| **WasteType** | Master list of collectible waste categories. |
| **TruckType** | Mapping of truck types to compatible waste types. |
| **Truck**     | Each collection truck with capacity and type. |
| **Facility**  | Drop-off facilities for specific waste types. |
| **Employee**  | Employees with IDs, names, hire dates. |
| **Driver**    | Employees qualified to drive specific truck types. |
| **Technician**| Employees qualified to maintain specific truck types. |
| **Maintenance** | Scheduled maintenance for trucks. |
| **Route**     | Planned collection routes per waste type. |
| **Stop**      | Addresses served on a route, including any assistance flag. |
| **Trip**      | Actual collection trips linking routes, trucks, drivers, and facilities. |

## Using the Schema
1. Run `waste_wrangler_schema.sql` to create all tables in PostgreSQL.
2. Load `waste_wrangler_data.sql` for sample data.
3. Use `main.py` (or `a2.py`) to connect via psycopg2 and run operations:
   - `connect` / `disconnect`
   - `schedule_trip`, `schedule_trips`
   - `update_technicians`
   - `workmate_sphere`
   - `schedule_maintenance`
   - `reroute_waste`

## Highlighting SQL Experience
- Designed a normalized relational schema enforcing referential integrity.
- Implemented complex scheduling logic and constraint checks using SQL.
- Utilized Python’s psycopg2 to execute parameterized queries, manage transactions,
  and build test utilities.

## Running the Example
```bash
python main.py
```
Provided for academic purposes as part of CSC343 (University of Toronto).
Please review the original course license terms before reusing this code.
