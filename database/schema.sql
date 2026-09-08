CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',

    UNIQUE (client_id, name)
);

CREATE TABLE devices (
    id SERIAL PRIMARY KEY,

    building_id INTEGER NOT NULL
        REFERENCES buildings(id)
        ON DELETE CASCADE,

    external_id TEXT NOT NULL,

    name TEXT,
    manufacturer TEXT,
    model TEXT,
    device_type TEXT,
    source_type TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (building_id, external_id)
);

CREATE TABLE datapoint_definitions (
    id SERIAL PRIMARY KEY,

    device_id INTEGER
        REFERENCES devices(id)
        ON DELETE CASCADE,

    key TEXT NOT NULL,
    description TEXT,

    value_type TEXT NOT NULL
        CHECK (value_type IN ('number', 'text', 'boolean')),

    unit TEXT,
    scale DOUBLE PRECISION DEFAULT 1,

    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,

    UNIQUE (device_id, key)
);

CREATE TABLE raw_messages (
    id BIGSERIAL PRIMARY KEY,

    device_id INTEGER
        REFERENCES devices(id)
        ON DELETE SET NULL,

    topic TEXT NOT NULL,

    payload JSONB,
    payload_text TEXT,

    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    processing_status TEXT NOT NULL DEFAULT 'received'
        CHECK (
            processing_status IN (
                'received',
                'processed',
                'invalid',
                'error'
            )
        ),

    error_message TEXT
);

CREATE TABLE measurements (
    id BIGSERIAL PRIMARY KEY,

    device_id INTEGER NOT NULL
        REFERENCES devices(id)
        ON DELETE CASCADE,

    datapoint_id INTEGER
        REFERENCES datapoint_definitions(id)
        ON DELETE SET NULL,

    raw_message_id BIGINT
        REFERENCES raw_messages(id)
        ON DELETE SET NULL,

    datapoint TEXT NOT NULL,

    numeric_value DOUBLE PRECISION,
    text_value TEXT,
    boolean_value BOOLEAN,

    measured_at TIMESTAMPTZ NOT NULL,

    quality TEXT NOT NULL DEFAULT 'valid'
        CHECK (
            quality IN (
                'valid',
                'suspicious',
                'invalid'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        device_id,
        datapoint,
        measured_at
    )
);

CREATE INDEX idx_measurements_device_time
ON measurements(device_id, measured_at);

CREATE INDEX idx_measurements_datapoint_time
ON measurements(datapoint, measured_at);

CREATE INDEX idx_raw_messages_received_at
ON raw_messages(received_at);