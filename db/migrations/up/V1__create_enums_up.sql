-- V1__create_enums_up.sql
DO $$
BEGIN
    -- Surface types for stadiums
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'surface_type') THEN
        CREATE TYPE surface_type AS ENUM (
            'Natural Grass',
            'Artificial Turf',
            'Hybrid Grass', 
            'Modular Turf'
        );
    END IF;

    -- Goal types
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'goal_type') THEN
        CREATE TYPE goal_type AS ENUM (
            'Open Play',
            'Free Kick',
            'Penalty',
            'Own Goal'
        );
    END IF;

    -- Foul types
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'foul_type') THEN
        CREATE TYPE foul_type AS ENUM (
            'Warning',
            'Foul',
            'Yellow Card',
            'Red Card'
        );
    END IF;

    -- Injury types
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'injury_type') THEN
        CREATE TYPE injury_type AS ENUM (
            'Muscular',
            'Joint',
            'Fracture',
            'Concussion',
            'Ligament Rupture'
        );
    END IF;

    -- Contract statuses
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contract_status') THEN
        CREATE TYPE contract_status AS ENUM (
            'Active',
            'Terminated',
            'Suspended'
        );
    END IF;

    -- Transfer types
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transfer_type') THEN
        CREATE TYPE transfer_type AS ENUM (
            'Purchase',
            'Loan',
            'Free Agent',
            'Exchange'
        );
    END IF;

    -- Player positions
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'player_position') THEN
        CREATE TYPE player_position AS ENUM (
            'GK', 'SW', 'CB', 'LCB', 'RCB', 'LB', 'RB', 'LWB', 'RWB',
            'LDM', 'CDM', 'RDM', 'LM', 'LCM', 'CM', 'RCM', 'LAM', 'CAM',
            'RAM', 'RM', 'RW', 'LW', 'CF', 'LS', 'RS', 'ST'
        );
    END IF;
END $$;