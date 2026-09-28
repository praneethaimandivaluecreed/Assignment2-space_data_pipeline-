USE [student4];
GO

IF OBJECT_ID(N'dbo.launches', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.launches
    (
        launch_id NVARCHAR(100) NOT NULL PRIMARY KEY,
        launch_name NVARCHAR(500) NOT NULL,
        launch_datetime DATETIMEOFFSET NOT NULL,
        status_id INT,
        status_name NVARCHAR(255),
        launch_probability FLOAT,
        weather_concerns NVARCHAR(MAX),
        failure_reason NVARCHAR(MAX),
        agency_id INT,
        launcher_configuration_id INT,
        pad_id INT,
        mission_name NVARCHAR(500),
        mission_type NVARCHAR(255),
        launch_year INT,
        launch_month INT,
        is_successful BIT,

        CONSTRAINT FK_launches_agencies
            FOREIGN KEY (agency_id)
            REFERENCES dbo.agencies(agency_id),

        CONSTRAINT FK_launches_launcher_configurations
            FOREIGN KEY (launcher_configuration_id)
            REFERENCES dbo.launcher_configurations(
                launcher_configuration_id
            ),

        CONSTRAINT FK_launches_pads
            FOREIGN KEY (pad_id)
            REFERENCES dbo.pads(pad_id)
    );
END;
GO
