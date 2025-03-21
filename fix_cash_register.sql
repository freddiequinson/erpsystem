-- Add is_active column to pos_cash_registers table if it doesn't exist
ALTER TABLE pos_cash_registers ADD COLUMN is_active BOOLEAN DEFAULT 1;
