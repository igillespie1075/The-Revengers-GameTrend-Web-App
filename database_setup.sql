CREATE DATABASE IF NOT EXISTS GamingTrends;

USE GamingTrends;

CREATE TABLE platforms (
    platform_id INT AUTO_INCREMENT PRIMARY KEY,
    platform_name VARCHAR(50) NOT NULL UNIQUE,
    platform_url VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE games (
    game_id INT AUTO_INCREMENT PRIMARY KEY,
    game_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    platform_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (platform_id)
        REFERENCES platforms(platform_id)
);

CREATE TABLE responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT NOT NULL,
    game_id INT NOT NULL,

    response_type ENUM(
        'favorite',
        'most_played',
        'currently_playing'
    ) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (submission_id)
        REFERENCES submissions(submission_id),

    FOREIGN KEY (game_id)
        REFERENCES games(game_id),

    UNIQUE (submission_id, response_type)
);

INSERT INTO platforms (platform_name)
VALUES
    ('PC'),
    ('PlayStation'),
    ('Xbox'),
    ('Nintendo Switch');

INSERT INTO games (game_name)
VALUES
    ('Minecraft'),
    ('Fortnite'),
    ('Roblox'),
    ('Elden Ring'),
    ('Valorant'),
    ('Rocket League'),
    ('The Legend of Zelda: Ocarina of Time'),
	('Tony Hawk''s Pro Skater 2'),
	('Grand Theft Auto IV'),
	('SoulCalibur'),
	('Super Mario Galaxy'),
	('Super Mario Galaxy 2'),
	('Red Dead Redemption 2'),
	('Grand Theft Auto V'),
	('Disco Elysium: The Final Cut'),
	('The Legend of Zelda: Breath of the Wild'),
	('Tony Hawk''s Pro Skater 3'),
	('Perfect Dark'),
	('Metroid Prime'),
	('Grand Theft Auto III'),
	('Super Mario Odyssey'),
	('Halo: Combat Evolved'),
	('NFL 2K1'),
	('Half-Life 2'),
	('BioShock'),
	('GoldenEye 007'),
	('Uncharted 2: Among Thieves'),
	('Resident Evil 4'),
	('Metal Gear Solid 2: Sons of Liberty'),
	('The Orange Box'),
	('Batman: Arkham City'),
	('Tekken 3'),
	('Mass Effect 2'),
	('The Legend of Zelda: Twilight Princess'),
	('Baldur''s Gate 3'),
	('The Last of Us'),
	('The Last of Us Part II'),
	('God of War'),
	('God of War Ragnarök'),
	('Portal 2'),
	('Half-Life'),
	('Chrono Trigger'),
	('Final Fantasy VII'),
	('Final Fantasy IX'),
	('Final Fantasy X'),
	('Persona 5 Royal'),
	('Persona 4 Golden'),
	('Persona 3 Reload'),
	('Bloodborne'),
	('Dark Souls'),
	('Dark Souls III'),
	('Sekiro: Shadows Die Twice'),
	('Demon''s Souls'),
	('The Witcher 3: Wild Hunt'),
	('Cyberpunk 2077'),
	('Red Dead Redemption'),
	('Skyrim'),
	('Oblivion'),
	('Morrowind'),
	('Fallout 3'),
	('Fallout: New Vegas'),
	('Mass Effect'),
	('Mass Effect 3'),
	('Dragon Age: Origins'),
	('Star Wars: Knights of the Old Republic'),
	('Divinity: Original Sin II'),
	('Hades'),
	('Hollow Knight'),
	('Celeste'),
	('Undertale'),
	('Stardew Valley'),	
	('Terraria'),
	('Super Mario 64'),
	('Super Mario Bros. 3'),
	('Super Mario World'),
	('The Legend of Zelda: A Link to the Past'),
	('The Legend of Zelda: Majora''s Mask'),
	('The Legend of Zelda: The Wind Waker'),
	('The Legend of Zelda: Tears of the Kingdom'),
	('Metroid Dread'),
	('Super Metroid'),
	('Castlevania: Symphony of the Night'),
	('Resident Evil 2'),
	('Resident Evil 2 Remake'),
	('Resident Evil 4 Remake'),
	('Silent Hill 2'),
	('Dead Space'),
	('Dead Space Remake'),
	('DOOM'),
	('DOOM Eternal'),
	('Quake'),
	('Portal'),
	('Left 4 Dead 2'),
	('Counter-Strike'),
	('Counter-Strike 2'),
	('Overwatch'),
	('Street Fighter II'),
	('Street Fighter 6'),
	('Super Smash Bros. Ultimate'),
	('Mario Kart 8 Deluxe'),
	('Animal Crossing: New Horizons');