USE [student4];
GO

IF OBJECT_ID(N'dbo.pads', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.pads
    (
        pad_id INT NOT NULL PRIMARY KEY,
        pad_name NVARCHAR(500) NOT NULL,
        active BIT,
        latitude FLOAT,
        longitude FLOAT,
        country NVARCHAR(255),
        location_id INT,
        location_name NVARCHAR(500),
        total_launch_count INT,
        orbital_launch_attempt_count INT,
        fastest_turnaround NVARCHAR(255)
    );
END;
GO
