CREATE TABLE IF NOT EXISTS users (
	user_id	BIGINT PRIMARY KEY,
  name TEXT,
	role VARCHAR(10),
	birth_datetime TEXT,
	birth_location_id INTEGER,
	current_location_id INTEGER,
  every_day_prediction_time TEXT,
  subscription_end_date TEXT,
  gender TEXT
);

CREATE TABLE IF NOT EXISTS locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, 
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

CREATE TABLE IF NOT EXISTS general_predictions (
  date TEXT PRIMARY KEY,
  prediction TEXT
);

CREATE TABLE viewed_predictions (
  user_id INTEGER NOT NULL,
  prediction_date TEXT NOT NULL,
  view_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(user_id, prediction_date),
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);


--CREATE TABLE IF NOT EXISTS mandatory_sub_channels (
--    channel_id INT PRIMARY KEY,
--    title VARCHAR(256),
--    invite_link VARCHAR(256)
--);
