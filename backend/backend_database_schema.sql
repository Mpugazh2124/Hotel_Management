IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'hotel_management')
BEGIN
    CREATE DATABASE hotel_management;
END;
GO

USE hotel_management;
GO

-- Bookings Table
CREATE TABLE Bookings (
    booking_id INT IDENTITY(1,1) PRIMARY KEY,
    room_number INT NOT NULL,
    customer_id INT NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    room_type VARCHAR(50), 
    price_per_day DECIMAL(10,2),
    total_price AS (DATEDIFF(DAY, check_in_date, ISNULL(check_out_date, check_in_date)) * ISNULL(price_per_day, 0)) PERSISTED,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (room_number) REFERENCES Rooms(room_number) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);
