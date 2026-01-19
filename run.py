from flask import Flask, request, render_template, redirect, url_for, flash
from datetime import datetime
import mysql.connector
import logging
import os
from dotenv import load_dotenv
load_dotenv()
password = os.getenv("DB_PASSWORD")


# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask("hotel_mang", template_folder="frontend/templates")
# Removed CSRFProtect setup
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

booked_rooms = []
food_items = [
    {"food_name": "Pizza", "price": 250},
    {"food_name": "Burger", "price": 150},
    {"food_name": "Pasta", "price": 200},
    {"food_name": "Fries", "price": 100},
    {"food_name": "Coke", "price": 50},
    {"food_name": "Idly", "price": 20},
    {"food_name": "Dosa", "price": 40},
    {"food_name": "Pongal", "price": 30},
    {"food_name": "Vada", "price": 20},
    {"food_name": "Poori", "price": 30},
    {"food_name": "Chapathi", "price": 40},
    {"food_name": "Parotta", "price": 30},
    {"food_name": "Kothu Parotta", "price": 50},
    {"food_name": "Chicken 65", "price": 100},
    {"food_name": "Chicken Lollipop", "price": 120},
    {"food_name": "Chicken Noodles", "price": 150},
    {"food_name": "Chicken Fried Rice", "price": 130},
    {"food_name": "Chicken Manchurian", "price": 140},
    {"food_name": "Chicken Biryani", "price": 200},
    {"food_name": "Mutton Biryani", "price": 250},
    {"food_name": "Egg Biryani", "price": 150},
    {"food_name": "Veg Biryani", "price": 100},
    {"food_name": "Paneer Biryani", "price": 150},
    {"food_name": "Veg Fried Rice", "price": 100},
    {"food_name": "Paneer Fried Rice", "price": 150},
    {"food_name": "Veg Noodles", "price": 100},
    {"food_name": "Paneer Noodles", "price": 150},
    {"food_name": "Veg Manchurian", "price": 100},
    {"food_name": "Veg Briyani", "price": 70},
    {"food_name": "Chilli mealmaker", "price": 100},
]

# Establish a connection to the database
db_config = {
    'host': 'localhost',
    'user': 'root',  
    'password': password,  
    'database': 'hotel_management'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Insert a booked room into the database
def insert_booked_room(room_number, customer_name, room_type, from_date, to_date, price_per_day, total_price):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Validate room type against the Rooms table
        cursor.execute("SELECT type FROM Rooms WHERE room_number = %s", (room_number,))
        room = cursor.fetchone()
        if not room:
            raise ValueError(f"Room number {room_number} does not exist.")
        if room[0] != room_type:
            raise ValueError(f"Room type mismatch for room number {room_number}. Expected: {room[0]}.")

        # Check if the room is available
        cursor.execute("SELECT availability FROM Rooms WHERE room_number = %s", (room_number,))
        room = cursor.fetchone()
        if not room:
            raise ValueError(f"Room number {room_number} does not exist.")
        if not room[0]:  # Room is not available
            raise ValueError(f"Room number {room_number} is already booked.")

        # Insert customer details
        cursor.execute(
            "INSERT INTO Customers (name) VALUES (%s)",
            (customer_name,)
        )
        customer_id = cursor.lastrowid

        # Insert booking details
        cursor.execute(
            """
            INSERT INTO Bookings (room_number, customer_id, check_in_date, check_out_date, room_type, price_per_day, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (room_number, customer_id, from_date, to_date, room_type, price_per_day, total_price)
        )

        # Update room availability
        cursor.execute(
            "UPDATE Rooms SET availability = FALSE WHERE room_number = %s",
            (room_number,)
        )

        connection.commit()
    except mysql.connector.errors.IntegrityError as e:
        connection.rollback()
        if "a foreign key constraint fails" in str(e):
            raise ValueError(f"Room number {room_number} does not exist in the Rooms table.")
        else:
            raise e
    except ValueError as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

# Fetch all booked rooms from the database
def fetch_all_booked_rooms():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT 
                b.room_number, 
                b.room_type,  # Fetch room_type from Bookings table
                r.price AS price_per_day, 
                c.name AS customer_name, 
                b.check_in_date AS from_date, 
                b.check_out_date AS to_date, 
                (DATEDIFF(b.check_out_date, b.check_in_date) * r.price) AS total_price
            FROM 
                Bookings b
            JOIN 
                Rooms r ON b.room_number = r.room_number  
            JOIN 
                Customers c ON b.customer_id = c.customer_id
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

def is_room_available(room_number):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT availability FROM Rooms WHERE room_number = %s",
            (room_number,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]  # Return availability status
        else:
            raise ValueError(f"Room number {room_number} does not exist.")
    finally:
        cursor.close()
        connection.close()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Handle menu selection
        if 'book_room' in request.form:
            return redirect(url_for('book_room'))
        elif 'view_booked_rooms' in request.form:
            return redirect(url_for('view_booked_room'))
        elif 'order_food' in request.form:
            return redirect(url_for('order_food'))
        elif 'view_food' in request.form:
            return redirect(url_for('view_food'))
        elif 'exit' in request.form:
            return render_template('exist.html')  

    
    return render_template('menu.html')

@app.route('/book-room', methods=['GET', 'POST'])
def book_room():
    room_number = None
    customer_name = None
    room_type = None
    from_date = None
    to_date = None
    price_per_day = None
    total_price = None
    error_message = None  # Variable to store error messages

    if request.method == 'POST':
        # Retrieve booking details from the form
        room_number = request.form.get('room_number')
        customer_name = request.form.get('customer_name')
        room_type = request.form.get('room_type')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        # Validate inputs
        if not room_number or not customer_name or not room_type or not from_date or not to_date:
            error_message = "All fields are required."
            return render_template('book_room.html', error_message=error_message)

        if not room_number.isdigit():
            error_message = "Room number must be a valid number."
            return render_template('book_room.html', error_message=error_message)

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Validate room type
            cursor.execute("SELECT type, availability FROM Rooms WHERE room_number = %s", (room_number,))
            room = cursor.fetchone()
            if not room:
                error_message = f"Room number {room_number} does not exist."
                return render_template('book_room.html', error_message=error_message)
            if room['type'] != room_type:
                error_message = f"Invalid room type for room number {room_number}. Expected: {room['type']}."
                return render_template('book_room.html', error_message=error_message)
            if not room['availability']:
                error_message = f"Room number {room_number} is already booked."
                return render_template('book_room.html', error_message=error_message)

            # Set price per day based on room type
            price_per_day = {"Single": 1000, "Double": 2000, "Suite": 5000}.get(room_type)
            if not price_per_day:
                error_message = "Invalid room type selected."
                return render_template('book_room.html', error_message=error_message)

            # Calculate total price
            from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
            days = (to_date_obj - from_date_obj).days
            if days <= 0:
                error_message = "Check-out date must be after check-in date."
                return render_template('book_room.html', error_message=error_message)
            total_price = days * price_per_day

            # Insert customer details
            cursor.execute("INSERT INTO Customers (name) VALUES (%s)", (customer_name,))
            customer_id = cursor.lastrowid

            # Insert booking details
            cursor.execute(
                """
                INSERT INTO Bookings (room_number, customer_id, check_in_date, check_out_date, room_type, price_per_day, total_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (room_number, customer_id, from_date, to_date, room_type, price_per_day, total_price)
            )

            # Update room availability
            cursor.execute("UPDATE Rooms SET availability = FALSE WHERE room_number = %s", (room_number,))

            connection.commit()

            # Redirect to booking confirmation page with details
            return redirect(url_for('booking_confirmation', 
                                    room_number=room_number, 
                                    customer_name=customer_name, 
                                    room_type=room_type, 
                                    from_date=from_date, 
                                    to_date=to_date, 
                                    price_per_day=price_per_day, 
                                    total_price=total_price))
        except mysql.connector.Error as e:
            connection.rollback()
            error_message = f"Database error: {str(e)}"
            return render_template('book_room.html', error_message=error_message)
        except ValueError as e:
            error_message = str(e)
            return render_template('book_room.html', error_message=error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_template('book_room.html', error_message=error_message)
        finally:
            cursor.close()
            connection.close()

    return render_template('book_room.html', error_message=error_message)

@app.route('/booking-confirmation')
def booking_confirmation():
    # Retrieve booking details from query parameters
    room_number = request.args.get('room_number')
    customer_name = request.args.get('customer_name')
    room_type = request.args.get('room_type')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    price_per_day = request.args.get('price_per_day', type=int)  # Ensure type conversion
    total_price = request.args.get('total_price', type=int)      # Ensure type conversion

    # Ensure all parameters are passed correctly
    if not all([room_number, customer_name, room_type, from_date, to_date, price_per_day, total_price]):
        return render_template('error.html', message="Missing booking details.")  # Use an error template

    return render_template(
        'booking_confirmation.html',
        room_number=room_number,
        customer_name=customer_name,
        room_type=room_type,
        from_date=from_date,
        to_date=to_date,
        price_per_day=price_per_day,
        total_price=total_price
    )

@app.route('/view-booked-room')
def view_booked_room():
    try:
        # Fetch booked rooms from the database
        booked_rooms = fetch_all_booked_rooms()
        return render_template('view_booked_room.html', booked_rooms=booked_rooms)
    except Exception as e:
        logging.error(f"Error fetching booked rooms: {e}")
        return render_template('error.html', message="Unable to fetch booked rooms.")  # Use an error template

@app.route('/delete-booking/<int:room_id>', methods=['POST'])
def delete_booking(room_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Delete the booking for the given room_id
        cursor.execute("DELETE FROM Bookings WHERE room_number = %s", (room_id,))
        cursor.execute("UPDATE Rooms SET availability = TRUE WHERE room_number = %s", (room_id,))
        connection.commit()

        flash(f"Booking for room {room_id} has been successfully deleted.", "success")
    except Exception as e:
        connection.rollback()
        logging.error(f"Error deleting booking for room {room_id}: {e}")
        flash(f"An error occurred while deleting the booking: {e}", "danger")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('view_booked_room'))

@app.route('/order-food', methods=['GET', 'POST'])
def order_food():
    total_food_price = 0
    ordered_items = []
    if request.method == 'POST':
        for food in food_items:
            if food['food_name'] in request.form:
                ordered_items.append(food)
                total_food_price += food['price']
        return render_template('food_order_confirmation.html', ordered_items=ordered_items, total_food_price=total_food_price)
    return render_template('order_food.html', food_items=food_items)

@app.route('/view-food')
def view_food():
    return render_template('view_food.html', food_items=food_items)


@app.route('/rooms')
def rooms():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT room_number, type, price, availability FROM Rooms")
        room_data = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template('rooms.html', rooms=room_data)
    except Exception as e:
        logging.error(f"Error fetching room data: {e}")
        return render_template('error.html', message="Unable to fetch room data.")  # Use an error template

@app.route('/room-prices')
def room_prices():
    return '''
        <h2>Room Prices:</h2>
        <ul>
            <li>Single Room: ₹1000</li>
            <li>Double Room: ₹2000</li>
            <li>Suite: ₹5000</li>
        </ul>
    '''

if __name__ == '__main__':
    app.run(debug=True)
