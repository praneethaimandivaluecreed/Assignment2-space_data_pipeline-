USE [student4];
GO

IF OBJECT_ID(N'dbo.launcher_configurations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.launcher_configurations
    (
        launcher_configuration_id INT NOT NULL PRIMARY KEY,
        launcher_name NVARCHAR(255) NOT NULL,
        full_name NVARCHAR(500),
        variant NVARCHAR(255),
        manufacturer_id INT,
        manufacturer_name NVARCHAR(255),
        active BIT,
        reusable BIT
    );
END;
GO
