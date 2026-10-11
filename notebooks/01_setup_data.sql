-- Run in the Databricks SQL editor. If you change catalog/schema, change them in app.yaml too.
CREATE SCHEMA IF NOT EXISTS workspace.voice_demo;

CREATE OR REPLACE TABLE workspace.voice_demo.products (
  sku STRING, name_en STRING, name_fr STRING, unit STRING, aliases STRING);
INSERT INTO workspace.voice_demo.products VALUES
  ('KET-01', 'Ketchup',       'Ketchup',            'case', 'catsup,sauce tomate'),
  ('MAY-01', 'Mayonnaise',    'Mayonnaise',         'case', 'mayo'),
  ('MPL-01', 'Maple syrup',   'Sirop d\'érable',    'case', 'maple,sirop derable'),
  ('PBT-01', 'Peanut butter', 'Beurre d\'arachide', 'case', 'beurre de pinottes,beurre de peanut');

CREATE OR REPLACE TABLE workspace.voice_demo.inventory (sku STRING, on_hand INT, start_qty INT, reorder_pt INT);
INSERT INTO workspace.voice_demo.inventory VALUES
  ('KET-01', 40, 40, 14), ('MAY-01', 25, 25, 9), ('MPL-01', 30, 30, 11), ('PBT-01', 18, 18, 8);

CREATE OR REPLACE TABLE workspace.voice_demo.orders (
  order_id STRING, sku STRING, qty INT, status STRING, created_at TIMESTAMP, session_id STRING);

-- Run after the app exists: use its service principal application ID (app page, Authorization section).
-- GRANT USE CATALOG ON CATALOG workspace TO `<app-service-principal-id>`;
-- GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA workspace.voice_demo TO `<app-service-principal-id>`;