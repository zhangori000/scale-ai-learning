CREATE TABLE towns (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, city, state)
);

CREATE TABLE neighborhoods (
    id BIGSERIAL PRIMARY KEY,
    town_id BIGINT NOT NULL REFERENCES towns(id),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (town_id, name)
);

CREATE TABLE parties (
    id BIGSERIAL PRIMARY KEY,
    external_party_id TEXT NOT NULL UNIQUE,
    neighborhood_id BIGINT NOT NULL REFERENCES neighborhoods(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_time >= start_time)
);

CREATE TABLE neighborhood_stats_daily (
    service_day DATE NOT NULL,
    neighborhood_id BIGINT NOT NULL REFERENCES neighborhoods(id),
    window_start_hour SMALLINT NOT NULL CHECK (window_start_hour BETWEEN 0 AND 23),
    window_end_hour SMALLINT NOT NULL CHECK (window_end_hour BETWEEN 0 AND 24),
    party_count INTEGER NOT NULL CHECK (party_count >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (service_day, neighborhood_id)
);

CREATE TABLE town_stats_daily (
    service_day DATE NOT NULL,
    town_id BIGINT NOT NULL REFERENCES towns(id),
    deadzone_hours INTEGER NOT NULL CHECK (deadzone_hours >= 0),
    merged_window_count INTEGER NOT NULL CHECK (merged_window_count >= 0),
    first_party_hour SMALLINT,
    last_party_hour SMALLINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (service_day, town_id)
);

CREATE INDEX idx_parties_start_time ON parties (start_time);
CREATE INDEX idx_parties_neighborhood_time ON parties (neighborhood_id, start_time);
CREATE INDEX idx_neighborhoods_town_id ON neighborhoods (town_id);
