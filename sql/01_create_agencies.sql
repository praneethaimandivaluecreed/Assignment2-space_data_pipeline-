USE [student4];
GO

IF OBJECT_ID(N'dbo.agencies', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.agencies
    (
        agency_id INT NOT NULL PRIMARY KEY,
        agency_name NVARCHAR(255) NOT NULL,
        abbreviation NVARCHAR(100),
        agency_type NVARCHAR(255),
        country NVARCHAR(MAX),
        founding_year INT
    );
END;
GO
