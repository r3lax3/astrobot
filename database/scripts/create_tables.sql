CREATE TABLE IF NOT EXISTS users (
	user_id	BIGINT PRIMARY KEY,
	role VARCHAR(10),
	birth_datetime TEXT,
	birth_location_id INT,
	current_location_id INT
);

CREATE TABLE IF NOT EXISTS locations (
    id INT PRIMARY KEY,
    type TEXT,
	longitude REAL,
	latitude REAL
);

CREATE TABLE IF NOT EXISTS interpretations (
    natal_planet TEXT,
    transit_planet TEXT,
    aspect TEXT,
    interpretation TEXT,
    PRIMARY KEY (natal_planet, transit_planet, aspect)
);

--CREATE TABLE IF NOT EXISTS mandatory_sub_channels (
--    channel_id INT PRIMARY KEY,
--    title VARCHAR(256),
--    invite_link VARCHAR(256)
--);
